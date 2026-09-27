"""
Day 01 — Connect to Gemini with an API key and print its response.

Run:  python week-01/hello_bot.py
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Read GEMINI_API_KEY from the .env file in the project root
load_dotenv()

# Try the main model first; if it's busy, fall back to the lighter one.
MODELS = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
PROMPT = "My name is Vamsi and I have a dog named Leo. Write a short story about us in 5 sentences. Make it funny and heartwarming."

# Wait between attempts: starts at 2s, doubles each round, never more than 60s
FIRST_DELAY = 2
MAX_DELAY = 60


def is_temporary(error):
    """True for errors worth retrying: server overload (5xx) or rate limits (429)."""
    return isinstance(error, errors.ServerError) or error.code == 429


def generate_with_retry(client, prompt):
    """Keep trying each model in turn until one returns a response. Ctrl+C to stop."""
    delay = FIRST_DELAY
    attempt = 1
    while True:
        for model in MODELS:
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return model, response
            except errors.APIError as e:
                if not is_temporary(e):
                    raise  # e.g. bad API key or unknown model — retrying won't help
                print(f"Attempt {attempt}: {model} unavailable ({e.code} {e.status})")
                attempt += 1

        print(f"All models busy. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, MAX_DELAY)


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        raise SystemExit("GEMINI_API_KEY is not set. Add it to the .env file (see .env.example).")

    client = genai.Client(api_key=api_key)

    model, response = generate_with_retry(client, PROMPT)

    print("Connected to Gemini successfully!\n")
    print(f"Model : {model}")
    print(f"Prompt: {PROMPT}\n")
    print("Response:")
    print(response.text)


if __name__ == "__main__":
    main()
