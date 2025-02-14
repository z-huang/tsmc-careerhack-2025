from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from config import PROJECT_ID, LOCATION

aiplatform.init(project=PROJECT_ID, location=LOCATION)

MAX_OUTPUT_TOKENS = 256
TEMPERATURE = 0.7
TOP_P = 0.9
TOP_K = 40

vertexai.init(project=PROJECT_ID, location=LOCATION)

generation_config = {
    "candidate_count": 1,
    "max_output_tokens": MAX_OUTPUT_TOKENS,
    "temperature": TEMPERATURE,
    "top_p": TOP_P,
    "top_k": TOP_K,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}


def translate_text(text: str, target_lang: str, source_lang=None) -> str:
    """
    Translates `text` from `source_lang` to `target_lang` using Gemini model.
    """
    model = GenerativeModel("gemini-2.0-flash-001")

    if not source_lang:
        prompt = f""":{text}\n{target_lang}:"""
    else:
        prompt = f"""{source_lang}: {text}\n{target_lang}:"""

    response = model.generate_content(
        [prompt],
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    print(response.text.rstrip())
    return response.text.rstrip()


if __name__ == "__main__":
    text = "Happy Birthday To You"
    translated_text = translate_text(text, "French")
    translated_text = translate_text(text, "French", "English")
