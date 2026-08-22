from google import genai
from utils.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

# newest first; older names kept as fallbacks (availability changes over time)
EMBED_MODELS = ["gemini-embedding-001", "text-embedding-004", "embedding-001"]

_working = {"model": None}


def embed_text(text: str):
    # reuse whichever model worked on the first call
    if _working["model"]:
        resp = client.models.embed_content(model=_working["model"], contents=text)
        return resp.embeddings[0].values

    last_err = None
    for m in EMBED_MODELS:
        try:
            resp = client.models.embed_content(model=m, contents=text)
            _working["model"] = m
            return resp.embeddings[0].values
        except Exception as e:
            last_err = e
    raise last_err