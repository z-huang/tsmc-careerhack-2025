import asyncio
import re
from typing import Iterable, List, Tuple
from google.cloud import aiplatform
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
import vertexai
from vertexai.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
from models import MeetingContent
from proper_noun import ENGLISH_DICT, GERMAN_DICT, CHINESE_DICT, JAPANESE_DICT, DESC_DICT, ALL_PROPER_NOUNS
from config import PROJECT_ID, LOCATION

aiplatform.init(project=PROJECT_ID, location=LOCATION)

MAX_OUTPUT_TOKENS = 1024
TEMPERATURE = 0.7
TOP_P = 0.9
TOP_K = 40

vertexai.init(project=PROJECT_ID, location=LOCATION)
short_it_terms = [
    "AI",
    "API",
    "BI",
    "CI/CD",
    "Cloud",
    "DevOps",
    "Edge",
    "GenAI",
    "GPU",
    "IoT",
    "LLM",
    "ML",
    "NLP",
    "No-Code",
    "Quantum",
    "RAG",
    "SaaS",
    "Sensor",
    "Serverless",
    "SIEM",
    "SOC",
    "SSD",
    "TinyML",
    "VectorDB",
    "Zero Trust"
]
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


def translate_text(text: str, target_lang: str) -> str:
    prompt = (
        "## System\n"
        "You are an AI that translates text into a specified target language while preserving and correctly spelling proper nouns.\n"

        "## Input\n"
        "**Proper Nouns Dictionary (By Language)**\n"
        f"English: {ENGLISH_DICT}\n"
        f"Chinese: {CHINESE_DICT}\n"
        f"German: {GERMAN_DICT}\n"
        f"Japanese: {JAPANESE_DICT}\n\n"
        f"Descriptions (in English): {DESC_DICT}\n\n"
        f"**Target Language:** {target_lang}\n"
        f"**Text to Translate:**\n{text}\n\n"

        "## Task\n"
        "1. Translate the input text into the target language.\n"
        "2. Ensure that proper nouns from the provided dictionary remain unchanged and are spelled correctly.\n"
        "3. Maintain the natural flow and grammar of the target language while considering multi-language text input.\n"
        "4. If a proper noun is ambiguous, infer the correct term from context.\n\n"

        "## Response Format (Strict Output)**\n"
        "**Translated Text:**\n"
        "[Translation of the input text into the target language with proper noun preservation]\n\n"

        "**Input Example:**\n"
        "I am using BigQuery for data analysis and testing クラウドらん.\n\n"

        "**Expected Output (for Japanese translation):**\n"
        "**Translated Text:**\n"
        "私は BigQuery を使ってデータ分析を行い、クラウドランをテストしています。\n\n"

        "**Ensure that the output is strictly just the translated text with no extra formatting or explanations!**"
    )

    match = None
    extracted = ""
    while match is None:
        response = model.generate_content(
            [prompt],
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        match = re.search(r"\*\*Translated Text:\*\*\n(.+)", response.text, re.DOTALL)
        if match:
            extracted = match.group(1)

    return extracted.rstrip('\n')


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
    Fixes speech recognition errors and ensures grammatical correctness.

    Returns:
        str: Merged sentence
    """
    prompt = (
        "## System\n"
        "You are an AI that merges overlapping sentences while preserving meaning and fluency. "
        "The context is a meeting record where participants may switch languages, especially for technical terms.\n"
        "Ensure grammatical correctness and fix speech recognition errors while maintaining multilingual integrity.\n"
        "\n"
        "## Input\n"
        f"Sentence PRE: {A}\n"
        f"Sentence SUF: {B}\n"
        f"Confidence of Sentence SUF: {conf} (-1 if undefined)\n"
        "Pre must go before Suf, and Pre might overlap with Suf.\n"
        "\n"
        "## Task\n"
        "1. Identify language(s) and detect overlaps.\n"
        "2. Correct speech recognition errors without altering meaning while trying not to delete stuff.\n"
        "3. Ensure the merged sentence is natural and grammatically correct. If a phrase is wierd in CHINESE, it is likely ENGLISH!!!\n"
        "\n"
        "## Thought Process\n"
        "1. Identify overlapping words or phrases.\n"
        "2. Detect and fix misrecognitions or cut-off phrases.\n"
        "3. Ensure the merged sentence is fluent and self-contained.\n"
        "\n"
        "## Response Format\n"
        "### Thought Process ###\n"
        "[Explain how you identified errors and merged the PRE and SUF strings]\n"
        "### Merged Text ###\n"
        "[Full merged sentence]\n"
        "### End ###\n"
        "\n"
        "## Reference Proper Nouns\n"
        f"English: {ENGLISH_DICT}\n"
        f"Chinese: {CHINESE_DICT}\n"
        f"German: {GERMAN_DICT}\n"
        f"Japanese: {JAPANESE_DICT}\n"
        f"Descriptions: {DESC_DICT}\n\n"
        "## Common IT Terms\n"
        f"common_it_terms = {short_it_terms}\n\n"
    )

    match = None
    while match is None:
        response = model.generate_content(
            [prompt],
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        match = re.search(r"### Merged Text ###\n(.*?)\n### End ###",
                          response.text, re.DOTALL)
        merged_text = match.group(1).strip() if match else ""

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


def chat(meeting_records: Iterable[MeetingContent], prompt):
    meeting_raw_text = '\n'.join([f"""\
Time: {record.time}
Text:
{record.message}
""" for record in meeting_records])

    """
    Calls Gemini to ask a question about a multi-lingual meeting record.
    Ensures proper nouns are correctly spelled before generating an answer.

    Args:
    - meeting_record (str): The full meeting transcript in multiple languages.
    - prompt (str): The question to ask about the meeting.

    Returns:
    - str: Gemini's response.
    """

    formatted_prompt = f"""
    ## System
    You are an AI assistant analyzing a multilingual meeting record. Your task is to answer questions about the meeting while preserving important details from all languages.

    ## Corrected Meeting Record
    {meeting_raw_text}

    ## Question
    {prompt}

    ## Instructions
    - The meeting may contain multiple languages, including English, Chinese, German, and Japanese.
    - Ensure your response is accurate and does not lose key details.
    - If needed, infer meaning across different languages while keeping the response in the most relevant language.
    
    ## Response
    [Answer here]
    """

    response = model.generate_content(
        [formatted_prompt],
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    return response.text.strip()


if __name__ == "__main__":
    text = "Happy Birthday To You"
    translated_text = translate_text(text, "French")
    translated_text = translate_text(text, "French", "English")
