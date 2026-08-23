import os
import logging
import streamlit as st
from google import genai

# Read API key from environment OR Streamlit secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

MODEL = "gemini-3.1-flash-lite"

# Initialize client only if key exists (prevents crash on Cloud)
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# Keep the terminal clean: only show real errors from the SDK
logging.getLogger("google.genai").setLevel(logging.ERROR)


def generate_json(prompt, system_instruction=""):
    """Generate JSON from Gemini with proper error handling."""
    if client is None:
        raise ValueError("GEMINI_API_KEY is missing. Add it to .env (local) or Streamlit Secrets (cloud).")
    
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"system_instruction": system_instruction} if system_instruction else None
    )
    
    # Parse JSON from response
    import json
    import re
    text = response.text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Extract JSON from markdown fences if present
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in text
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not parse JSON from response: {text[:200]}")