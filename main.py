from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
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
