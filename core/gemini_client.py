import json
import logging
from google import genai
from google.genai import types
from utils.config import GEMINI_API_KEY

MODEL = "gemini-3.1-flash-lite"

client = genai.Client(api_key=GEMINI_API_KEY)

# keep the terminal clean: only show real errors from the SDK
logging.getLogger("google.genai").setLevel(logging.ERROR)


def generate_text(prompt, system_instruction=None):
    # Chat API = the SDK's recommended path (no AFC warning)
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        ),
    )
    resp = chat.send_message(prompt)
    return resp.text


def generate_json(prompt, system_instruction=None):
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            response_mime_type="application/json",
        ),
    )
    resp = chat.send_message(prompt)
    return json.loads(resp.text)