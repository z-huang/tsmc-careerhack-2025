import io
import math
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from pydub import AudioSegment
from pydub.silence import detect_silence
from models import Meeting, MeetingContent, Settings
import gemini

app = FastAPI()


class TranslateInput(BaseModel):
    text: str
    target_lang: str


class SetLanguageInput(BaseModel):
    language: str


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

    seg_i = 0

    processed_time = 0
    block_text = ''
    block_i = 0

    try:
        while True:
            audio_data += await websocket.receive_bytes()
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format='webm')
            silences = [
                [0, 0]] + detect_silence(audio, min_silence_len=1000, silence_thresh=-40) + [[math.inf, math.inf]]
            print(silences)

            while len(audio) - processed_time > WIN_SIZE:
                seg_start = silences[seg_i][1]
                seg_end = math.inf
                for i, (start, end) in enumerate(silences):
                    if seg_start == end:
                        seg_end = silences[i + 1][0]

                buffer = io.BytesIO()
                start = max(seg_start, processed_time)
                end = min(seg_end, processed_time + WIN_SIZE)
                if end - start >= 1000:
                    audio[start:end].export(buffer, format='mp3')

                    text, confidence = await gemini.speech2text(buffer.getvalue())
                    if confidence != -1:
                        block_text = gemini.merge_text(block_text, text, confidence)
                        block_text = gemini.correct_keywords(block_text)
                        keywords = gemini.find_keywords(block_text)
                        await websocket.send_json({
                            'block_id': block_i,
                            'text': block_text,
                            'keywords': [
                                {
                                    'id': id,
                                    'start': start,
                                    'end': end
                                }
                                for id, start, end in keywords
                            ]
                        })

                processed_time += HOP_SIZE
                while processed_time >= silences[seg_i + 1][0]:
                    seg_i += 1
                    if block_text:
                        block_text = ''
                        block_i += 1

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


@app.get("/get_language")
async def get_language(db: Session = Depends(get_db)):
    setting = db.query(Settings).filter(Settings.key == "language").first()
    if not setting:
        raise HTTPException(status_code=404, detail="Language setting not found")
    return {"result": setting.value}


@app.post("/set_language")
async def set_language(input_data: SetLanguageInput, db: Session = Depends(get_db)):
    setting = db.query(Settings).filter(Settings.key == "language").first()
    if setting:
        setting.value = input_data.language
    else:
        setting = Settings(key="language", value=input_data.language)
        db.add(setting)

    db.commit()
    return {"success": True}
