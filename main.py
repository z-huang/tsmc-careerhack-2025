import datetime
import io
import tempfile
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
import ipdb
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
from pydub import AudioSegment
from models import Meeting, MeetingContent
import gemini

app = FastAPI()


class TranslateInput(BaseModel):
    text: str
    target_lang: str


@app.post("/translate")
async def translate(input_data: TranslateInput):
    translated_text = gemini.translate_text(
        input_data.text,
        target_lang=input_data.target_lang)

    return {
        "text": translated_text,
        "keywords": 'NotImplemented'
    }

WIN_SIZE = 3000
HOP_SIZE = 2000


@app.websocket("/ws/transcript")
async def transcript(websocket: WebSocket):
    await websocket.accept()
    audio_data = b''
    current_time = 0
    block_text = ''

    try:
        while True:
            audio_data += await websocket.receive_bytes()
            audio: AudioSegment = AudioSegment.from_file(
                io.BytesIO(audio_data), format='webm')

            while len(audio) - current_time > WIN_SIZE:
                buffer = io.BytesIO()
                audio[current_time:current_time + WIN_SIZE].export(buffer, format='mp3')
                current_time += HOP_SIZE

                answer, score = await gemini.speech2text(buffer.getvalue())
                block_text = gemini.merge_text(block_text, answer, score)
                await websocket.send_json({
                    'block_id': 1,
                    'text': block_text,
                    'keywords': []
                })

    except WebSocketDisconnect:
        print("Client disconnected.")


@app.post("/get_meetings")
async def get_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).all()
    return [
        {
            "meeting_id": m.meeting_id,
            "topic": m.topic,
            "date": m.date
        }
        for m in meetings
    ]


@app.post("/get_content")
async def get_content(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(MeetingContent).filter(
        MeetingContent.meeting_id == meeting_id).all()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return [
        {
            "message": m.message,
            "time": m.time
        }
        for m in meeting
    ]
