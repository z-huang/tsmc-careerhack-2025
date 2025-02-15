import datetime
import io
import math
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from pydub import AudioSegment
from pydub.silence import detect_silence
from models import Meeting, MeetingContent, Settings
import gemini

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.websocket("/ws/transcript/{meeting_id}")
async def transcript(websocket: WebSocket, meeting_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    audio_data = b''

    seg_i = 0

    processed_time = 0
    block_text = ''
    block_i = 0

    entry = None

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
                        entry = {
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
                        }
                        await websocket.send_json(entry)

                processed_time += HOP_SIZE
                while processed_time >= silences[seg_i + 1][0]:
                    seg_i += 1
                    if block_text:
                        block_text = ''
                        block_i += 1
                        row = MeetingContent(
                            meeting_id=meeting_id,
                            block_id=entry['block_id'],
                            message=entry['text'],
                            time=datetime.datetime.now(),
                        )
                        db.add(row)
                        db.commit()
                        entry = None

    except WebSocketDisconnect:
        if entry:
            row = MeetingContent(
                meeting_id=meeting_id,
                block_id=entry['block_id'],
                message=entry['text'],
                time=datetime.datetime.now(),
            )
            db.add(row)
            db.commit()
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


@app.post("/new_meeting")
async def create_meeting(db: Session = Depends(get_db)):
    new_meeting = Meeting(topic="", date=datetime.date.today())
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    return {
        "meeting_id": new_meeting.meeting_id,
        "topic": new_meeting.topic,
        "date": new_meeting.date.strftime("%Y-%m-%d")
    }


@app.get("/meeting_contents/{meeting_id}")
async def get_meeting_contents(meeting_id: str, db: Session = Depends(get_db)):
    contents = db.query(MeetingContent).filter(
        MeetingContent.meeting_id == meeting_id).all()

    return [
        {
            "id": content.id,
            "block_id": content.block_id,
            "message": content.message,
            "time": content.time.strftime("%H:%M:%S")
        }
        for content in contents
    ]


class ChatInput(BaseModel):
    meeting_id: int
    prompt: str


@app.get("/chat")
async def chat(input_data: ChatInput, db: Session = Depends(get_db)):
    contents = db.query(MeetingContent).filter(
        MeetingContent.meeting_id == input_data.meeting_id).all()
    result = gemini.chat(contents, input_data.prompt)
    return {"result": result}


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
