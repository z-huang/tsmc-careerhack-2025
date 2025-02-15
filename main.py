import datetime
import io
import math
import os
from fastapi import FastAPI, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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

WIN_SIZE = 4000
HOP_SIZE = 2000


@app.websocket("/ws/transcript/{meeting_id}")
async def transcript(websocket: WebSocket, meeting_id: int, db: Session = Depends(get_db)):
    await websocket.accept()
    audio_data = b''

    processed_time = 0
    block_text = ''
    block_i = db.query(func.coalesce(func.max(MeetingContent.block_id), -1)).filter(
        MeetingContent.meeting_id == meeting_id).scalar() + 1
    target_lang = db.query(Settings).filter(Settings.key == "language").first().value

    prev_k = []  # List to store last k tries
    k = 4  # Number of previous attempts to keep track of

    try:
        while True:
            audio_data += await websocket.receive_bytes()
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format='webm')

            while len(audio) - processed_time > WIN_SIZE:
                buffer = io.BytesIO()
                audio[processed_time:processed_time +
                      WIN_SIZE].export(buffer, format='mp3')

                text, confidence = await gemini.speech2text(buffer.getvalue())
                if confidence != -1:
                    tmp = gemini.merge_text(
                        prev_k[-1] if prev_k else "", text, confidence)
                    prev_k.append(tmp)
                    if len(prev_k) > k:
                        prev_k.pop(0)  # Maintain only last k tries

                    for j in range(min(map(len, prev_k)), -1, -1):
                        if j == 0 or len(prev_k) < k:
                            break
                        if all(entry[:j] == prev_k[0][:j] for entry in prev_k):
                            s = gemini.correct_keywords(prev_k[0][:j])
                            s = gemini.translate_text(s, target_lang)
                            keywords = gemini.find_keywords(s)
                            prev_k = [entry[j:] for entry in prev_k]
                            entry = {
                                'block_id': block_i,
                                'text': s,
                                'keywords': [
                                    {
                                        'id': id,
                                        'start': start,
                                        'end': end
                                    }
                                    for id, start, end in keywords
                                ]
                            }
                            block_i += 1
                            row = MeetingContent(
                                meeting_id=meeting_id,
                                block_id=entry['block_id'],
                                message=entry['text'],
                                time=datetime.datetime.now(),
                            )
                            db.add(row)
                            db.commit()
                            await websocket.send_json(entry)
                            break

                    s = gemini.correct_keywords(prev_k[-1]) 
                    s = gemini.translate_text(s, target_lang)
                    keywords = gemini.find_keywords(s)
                    entry = {
                        'block_id': block_i,
                        'text': s,
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

    except WebSocketDisconnect:
        if prev_k:
            s = gemini.correct_keywords(prev_k[-1])
            s = gemini.translate_text(s, target_lang)
            keywords = gemini.find_keywords(s)
            entry = {
                'block_id': block_i,
                'text': s,
                'keywords': [
                    {
                        'id': id,
                        'start': start,
                        'end': end
                    }
                    for id, start, end in keywords
                ]
            }
            block_i += 1
            row = MeetingContent(
                meeting_id=meeting_id,
                block_id=entry['block_id'],
                message=entry['text'],
                time=datetime.datetime.now(),
            )
            db.add(row)
            db.commit()
            # await websocket.send_json(entry)

    audio.export(f'output/meeting_{meeting_id}.mp3', format='mp3')

    print("Client disconnected.")

# @app.post("/upload_transcript/{meeting_id}")
# async def upload_transcript(meeting_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
#     audio_data = await file.read()
#     audio = AudioSegment.from_file(io.BytesIO(audio_data), format=file.filename.split('.')[-1])
    
    

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
    target_lang = db.query(Settings).filter(Settings.key == "language").first().value

    return [
        {
            "id": content.id,
            "block_id": content.block_id,
            "message": gemini.translate_text(content.message, target_lang),
            "time": content.time.strftime("%H:%M:%S")
        }
        for content in contents
    ]


class ChatInput(BaseModel):
    meeting_id: int
    prompt: str


@app.post("/chat")
async def chat(input_data: ChatInput, db: Session = Depends(get_db)):
    target_lang = db.query(Settings).filter(Settings.key == "language").first().value

    contents = db.query(MeetingContent).filter(
        MeetingContent.meeting_id == input_data.meeting_id).all()
    result = gemini.chat(contents, input_data.prompt)
    result = gemini.translate_text(result, target_lang)
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


@app.get("/search")
async def search(
    query: str = Query(..., min_length=1, description="Search keyword"),
    meeting_id: int | None = Query(None, description="Filter by meeting ID"),
    db: Session = Depends(get_db)
):
    search_query = db.query(MeetingContent).filter(
        MeetingContent.message.ilike(f"%{query}%"))

    if meeting_id is not None:
        search_query = search_query.filter(MeetingContent.meeting_id == meeting_id)

    results = search_query.limit(50).all()

    return [
        {
            'meeting_id': row.meeting_id,
            'text': row.message,
            'time': row.time
        }
        for row in results
    ]


@app.get("/download/{meeting_id}")
async def download_file(meeting_id: str):
    file_path = os.path.join('output', f'meeting_{meeting_id}.mp3')
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=f'meeting_{meeting_id}.mp3', media_type="audio/mp3")
    return {"error": "File not found"}
