import asyncio
import re
from typing import List, Tuple
from google.cloud import aiplatform
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from proper_noun import ENGLISH_DICT, GERMAN_DICT, CHINESE_DICT, JAPANESE_DICT, DESC_DICT, ALL_PROPER_NOUNS
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

model = GenerativeModel("gemini-2.0-flash-001")


def translate_text(text: str, target_lang: str, source_lang=None) -> str:
    """
    Translates `text` from `source_lang` to `target_lang` using Gemini model.
    """
    if not source_lang:
        prompt = f""":{text}\n{target_lang}:"""
    else:
        prompt = f"""{source_lang}: {text}\n{target_lang}:"""

    response = model.generate_content(
        [prompt],
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    return response.text.rstrip()


async def _recognize_audio(client, request):
    """Run speech recognition in a separate thread."""
    return await asyncio.to_thread(client.recognize, request=request)


async def speech2text(audio_content: bytes):
    client = SpeechClient()

    # Configure speech recognition settings
    config1 = cloud_speech.RecognitionConfig(
        explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
            encoding="MP3",
            sample_rate_hertz=48000,
            audio_channel_count=1
        ),
        # auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US", "cmn-Hant-TW", "de-DE"],
        model="long",
    )
    config2 = cloud_speech.RecognitionConfig(
        explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
            encoding="MP3",
            sample_rate_hertz=48000,
            audio_channel_count=1
        ),
        # auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US", "ja-JP", "cmn-Hant-TW"],
        model="long",
    )

    # Create a recognition request
    request1 = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        config=config1,
        content=audio_content,
    )
    request2 = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        config=config2,
        content=audio_content,
    )

    response1, response2 = await asyncio.gather(
        _recognize_audio(client, request1),
        _recognize_audio(client, request2)
    )

    answer = ""
    score = -1
    for result in response1.results:
        if result.alternatives:
            answer = result.alternatives[0].transcript
            score = result.alternatives[0].confidence
    for result in response2.results:
        if result.alternatives and result.alternatives[0].confidence > score:
            answer = result.alternatives[0].transcript
            score = result.alternatives[0].confidence

    return answer, score


def merge_text(A: str, B: str, conf=-1):
    """
    Merges two overlapping sentences while preserving the original language.
    Ensures the output is formatted for easy parsing and separates complete/incomplete parts.

    Returns:
        tuple: (complete_text, incomplete_text)
    """
    prompt = (
        "## System\n"
        "You are an AI that merges overlapping sentences while preserving meaning and fluency. "
        "The context is a meeting record, so it might contain different people speaking with different languages."
        "Fix speech recognition errors and ensure grammatical correctness.\n\n"

        "## Input\n"
        f"Sentence PRE (may be empty): {A}\n"
        f"Sentence SUF: {B}\n"
        f"Confidence of Sentence Suf: {conf} (-1 if undefined)"
        f"Pre must go before Suf, and Pre might overlap with Suf.\n\n"

        "## Task\n"
        "1. Identify the language(s) and detect overlaps.\n"
        "2. Correct speech recognition errors without altering meaning.\n"
        "3. Ensure the merged sentence is natural and grammatically correct.\n"
        # "4. Separate the text into **complete** (self-contained) and **incomplete** (needs more context) parts.\n"
        # "5. **Ensure the complete part appears at the beginning of the merged sentence, followed by the incomplete part.**\n\n"

        "## Thought Process\n"
        "1. Identify overlapping words or phrases.\n"
        "2. Check for misrecognitions or cut-off phrases.\n"
        # "3. Ensure the **complete part** is a full, independent thought and must appear first in the sentence.\n"
        # "4. Mark anything that requires more information as **incomplete**, and ensure it comes after the complete part.\n\n"

        "## Response Format\n"
        "### Thought Process ###\n"
        "[Explain how you identified errors and merge the PRE and SUF strings]\n"
        "### Merged Text ###\n"
        "[Full merged sentence]\n"
        "### End ###\n\n"
        # "### Complete Part ###\n"
        # "[Complete Part (must be at the start of the merged sentence)]\n"
        # "### Incomplete Part ###\n"
        # "[Incomplete Part (must follow the complete part)]\n"
        # "### End ###\n\n"

        # "**Complete Part Criteria:**\n"
        # "- A grammatically correct, natural sentence that stands alone.\n"
        # "- Must always appear at the **beginning** of the full sentence.\n"
        # "- Should not leave the reader expecting more information.\n"
        # "- Example incomplete phrase: 'This meeting is to ask evan'.\n"
        # "- Example complete sentence: 'This meeting aims to discuss company culture.'\n\n"
        # "- If the entire sentence is incomplete, leave the complete section empty.\n\n"

        # "**Incomplete Part Criteria:**\n"
        # "- Any phrase requiring additional context to be meaningful.\n"
        # "- Must always appear **after** the complete part in the full merged sentence.\n"
        # f"- This part should be as long as possible without exceeding {MAX_CONTENT_LENGTH} characters.\n\n"

        # "NOTE: The **Complete Part must be go before the **Incomplete Part**. Do not reorder.\n"
    )

    # Extract merged sentence

    match = None
    while match is None:
        response = model.generate_content(
            [prompt],
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        match = re.search(r"### Merged Text ###\n(.*?)\n### End ###",
                          response.text, re.DOTALL)
        # TODO: add something to check if the format is correct and provide more error detection

        merged_text = match.group(1).strip() if match else ""

    # Extract Complete Part
    # match = re.search(r"### Complete Part ###\n(.*?)\n### Incomplete Part ###", response.text, re.DOTALL)
    # complete_text = match.group(1).strip() if match else ""

    # Extract Incomplete Part
    # match = re.search(r"### Incomplete Part ###\n(.*?)\n### End ###", response.text, re.DOTALL)
    # incomplete_text = match.group(1).strip() if match else ""

    # Extract complete and incomplete parts
    '''
    print("Merged Sentence:", merged_text)
    print("Complete Part:", complete_text)
    print("Incomplete Part:", incomplete_text)
    print("Conf: ", conf)
    '''

    return merged_text


def correct_keywords(s: str):
    prompt = (
        "## System\n"
        "You are an AI that detects and corrects the spelling of known proper nouns in a given text.\n"
        "Your goal is to identify occurrences of proper nouns across multiple languages (English, Chinese, German, Japanese) and ensure they appear with the correct spelling while keeping the rest of the text unchanged.\n\n"

        "## Input\n"
        "**Proper Nouns (By Language)**\n"
        f"English: {ENGLISH_DICT}\n"
        f"Chinese: {CHINESE_DICT}\n"
        f"German: {GERMAN_DICT}\n"
        f"Japanese: {JAPANESE_DICT}\n\n"
        f"Descriptions (in English): {DESC_DICT}"

        "**Text to Analyze**\n"
        f"{s}\n\n"

        "## Task\n"
        "1. Identify any mentions of the provided proper nouns in the input text (even if they contain minor spelling errors or OCR recognition issues).\n"
        "2. Correct the spelling of detected proper nouns to match their official forms from the provided list.\n"
        "3. Keep the rest of the text unchanged.\n"
        "4. Ensure that the corrected text maintains the original meaning, language and fluency.\n\n"

        "## Response Format (Strict Output)**\n"
        "**Corrected Text:**\n"
        "[Corrected version of the input text with proper noun spellings fixed]\n\n"

        "**Input Text:**\n"
        "\"I am using bigquery for data analysis. Also testing クラウド らん for deployment.\"\n\n"

        "**Expected Response:**\n"
        "**Corrected Text:**\n"
        "\"I am using BigQuery for data analysis. Also testing クラウドラン for deployment.\"\n\n"

        "**Ensure that the output is strictly just the corrected text with no extra formatting or explanations!**"
    )
    match = None
    extracted = ""
    while match is None:
        response = model.generate_content(
            [prompt],
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        match = re.search(r"\*\*Corrected Text:\*\*\n(.+)", response.text, re.DOTALL)
        if match:
            extracted = match.group(1)

    return extracted.rstrip('\n')


def find_keywords(text) -> List[Tuple[int, int, int]]:
    """
    Identifies occurrences of proper nouns in the text and returns their positions.

    Args:
    - text (str): The input text to search within.
    - proper_noun_dicts (dict): A dictionary where keys are entry IDs, and values are dictionaries containing proper nouns in multiple languages.

    Returns:
    - List of tuples (proper_noun_id, start_position, end_position).
    """
    matches = []

    # Iterate over each entry ID and its proper nouns
    for entry_id, proper_nouns in ALL_PROPER_NOUNS.items():
        for lang, noun in proper_nouns.items():
            if noun:  # Ensure the noun exists
                # Use regex to find all occurrences of the noun in the text (case-sensitive)
                for match in re.finditer(rf'{re.escape(noun)}', text, re.IGNORECASE):
                    matches.append((entry_id, match.start(), match.start() + len(noun)))

    # Sort by position to maintain order
    matches.sort(key=lambda x: x[1])

    return sorted(set(matches))


if __name__ == "__main__":
    text = "Happy Birthday To You"
    translated_text = translate_text(text, "French")
    translated_text = translate_text(text, "French", "English")
