"""
Week 02 — A web page where you type a prompt, pick a Gemini model, and see the response.

Two parts work together:
  main.py            the server (FastAPI): serves the page and talks to Gemini
  static/index.html  the page: sends your prompt to the server and shows the reply

The API key stays on the server, so it never reaches the browser.

Run (from the week-02-add-chat-interface folder):
  cd week-02-add-chat-interface
  uvicorn main:app --reload --port 8000
Then open http://127.0.0.1:8000 in your browser. Ctrl+C stops the server.
"""

import os
import time
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from google import genai
from google.genai import errors
from pydantic import BaseModel

# Read GEMINI_API_KEY from the .env file in the project root
load_dotenv()

# Models the page offers in its dropdown. The first one is the default.
MODELS = {
    "gemini-3.8-flash": "Gemini 3.8 Flash — newest, fast and smart",
    "gemini-3.5-flash": "Gemini 3.5 Flash — a solid all-rounder",
    "gemini-3.5-flash-lite": "Gemini 3.5 Flash Lite — lightest and quickest",
}

# If the model is busy, try again a few times, waiting a little longer each time
ATTEMPTS = 3
FIRST_DELAY = 2

PAGE = Path(__file__).parent / "static" / "index.html"

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your-api-key-here":
    raise SystemExit("GEMINI_API_KEY is not set. Add it to the .env file (see .env.example).")

client = genai.Client(api_key=api_key)
app = FastAPI(title="Gemini Web Bot")


def is_temporary(error):
    """True for errors worth retrying: server overload (5xx) or rate limits (429)."""
    return isinstance(error, errors.ServerError) or error.code == 429


def generate_with_retry(model, prompt):
    """Ask the model, retrying a few times if it's busy. Raises the last error if all fail."""
    delay = FIRST_DELAY
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return client.models.generate_content(model=model, contents=prompt)
        except errors.APIError as e:
            if not is_temporary(e) or attempt == ATTEMPTS:
                raise  # e.g. bad API key, or still busy after the last attempt
            print(f"Attempt {attempt}: {model} busy ({e.code} {e.status}). Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2


# ---------------------------------------------------------------------------
# Routes: each function answers one URL
# ---------------------------------------------------------------------------


class AskRequest(BaseModel):
    """What the page sends to /api/ask. FastAPI checks the JSON has these fields."""

    prompt: str
    model: str


@app.get("/")
def home():
    """The web page itself."""
    return FileResponse(PAGE)


@app.get("/api/models")
def list_models():
    """The models for the page's dropdown."""
    return [{"id": model_id, "label": label} for model_id, label in MODELS.items()]


@app.post("/api/ask")
def ask(request: AskRequest):
    """Send the prompt to Gemini and return its reply as JSON."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Please type a prompt first.")
    if request.model not in MODELS:
        raise HTTPException(status_code=400, detail=f"Unknown model: {request.model}")

    start = time.time()
    try:
        response = generate_with_retry(request.model, request.prompt)
    except errors.APIError as e:
        if is_temporary(e):
            detail = f"{request.model} is busy right now. Try again in a minute, or pick another model."
            raise HTTPException(status_code=503, detail=detail)
        raise HTTPException(status_code=502, detail=f"Gemini error ({e.code} {e.status}): {e.message}")

    return {
        "model": request.model,
        "response": response.text,
        "seconds": round(time.time() - start, 1),
    }


# Lets `python main.py` work too, without typing the uvicorn command
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
