from fastapi import FastAPI
from pydantic import BaseModel
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
