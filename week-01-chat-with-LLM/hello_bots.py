"""
Week 01 — Say hello to an LLM of your choice and print its response.

Supported providers:
  gemini  Google Gemini         needs GEMINI_API_KEY     (free tier available)
  claude  Anthropic Claude      needs ANTHROPIC_API_KEY
  openai  OpenAI GPT            needs OPENAI_API_KEY
  ollama  Local model (Ollama)  no key; free, runs on your own machine

Run (from the project root):
  python week-01-chat-with-LLM/hello_bots.py                    # Gemini (the default)
  python week-01-chat-with-LLM/hello_bots.py --provider claude
  python week-01-chat-with-LLM/hello_bots.py --provider openai --model gpt-5.4-nano
  python week-01-chat-with-LLM/hello_bots.py --provider ollama --prompt "Tell me a joke"
  python week-01-chat-with-LLM/hello_bots.py --list             # show providers and models

Set LLM_PROVIDER in .env to change the default provider.
"""

import argparse
import os
import time

from dotenv import load_dotenv

# Read API keys (and optionally LLM_PROVIDER) from the .env file in the project root
load_dotenv()

PROMPT = "My name is Vamsi and I have a dog named Leo. Write a short story about us in 5 sentences. Make it funny and heartwarming."

# Wait between attempts: starts at 2s, doubles each round, never more than 60s
FIRST_DELAY = 2
MAX_DELAY = 60


# ---------------------------------------------------------------------------
# Providers
#
# Every provider class has the same shape, so the rest of the program doesn't
# care which LLM it is talking to:
#   models              models to try, in order (main model first, then fallbacks)
#   key_env             name of the environment variable holding the API key
#   ask(model, prompt)  send the prompt, return the reply as plain text
#   is_temporary(err)   True if the error is worth retrying (overload, rate limit)
#
# Each SDK is imported inside its class, so you only need to install the
# package for the provider you actually use.
# ---------------------------------------------------------------------------


class Gemini:
    name = "Google Gemini"
    key_env = "GEMINI_API_KEY"
    key_url = "https://aistudio.google.com/apikey"
    package = "google-genai"
    models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]

    def __init__(self, api_key):
        from google import genai

        self.client = genai.Client(api_key=api_key)

    def ask(self, model, prompt):
        response = self.client.models.generate_content(model=model, contents=prompt)
        return response.text

    def is_temporary(self, error):
        from google.genai import errors

        # Server overload (5xx) or rate limit (429)
        return isinstance(error, errors.ServerError) or (
            isinstance(error, errors.APIError) and error.code == 429
        )


class Claude:
    name = "Anthropic Claude"
    key_env = "ANTHROPIC_API_KEY"
    key_url = "https://console.anthropic.com/settings/keys"
    package = "anthropic"
    models = ["claude-opus-5", "claude-sonnet-5"]

    def __init__(self, api_key):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)

    def ask(self, model, prompt):
        # Opus 5 can decline a request it judges unsafe. "fallbacks" asks the
        # server to re-run a declined request on a model Anthropic recommends.
        safety_fallback = {}
        if model == "claude-opus-5":
            safety_fallback = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}

        response = self.client.beta.messages.create(
            model=model,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
            **safety_fallback,
        )
        if response.stop_reason == "refusal":
            return "(Claude declined to answer this prompt.)"
        # A reply is a list of content blocks; keep only the text ones
        return "".join(block.text for block in response.content if block.type == "text")

    def is_temporary(self, error):
        import anthropic

        if isinstance(error, anthropic.APIConnectionError):
            return True
        return isinstance(error, anthropic.APIStatusError) and (
            error.status_code == 429 or error.status_code >= 500
        )


class OpenAI:
    name = "OpenAI GPT"
    key_env = "OPENAI_API_KEY"
    key_url = "https://platform.openai.com/api-keys"
    package = "openai"
    models = ["gpt-5.4-mini", "gpt-5.4-nano"]
    base_url = None  # None = OpenAI's own servers

    def __init__(self, api_key):
        import openai

        self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)

    def ask(self, model, prompt):
        # Chat Completions is the most widely copied API shape: Ollama, Groq,
        # OpenRouter, DeepSeek and others accept the exact same call.
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def is_temporary(self, error):
        import openai

        if isinstance(error, openai.APIConnectionError):
            return True
        return isinstance(error, openai.APIStatusError) and (
            error.status_code == 429 or error.status_code >= 500
        )


class Ollama(OpenAI):
    """A model running on your own computer. Ollama speaks the OpenAI API."""

    name = "Ollama (local)"
    key_env = None  # no key needed
    key_url = None
    models = ["llama3.2:3b"]
    base_url = "http://localhost:11434/v1"

    def __init__(self, api_key):
        super().__init__(api_key="ollama")  # Ollama ignores the key, but the SDK insists on one

    def ask(self, model, prompt):
        import openai

        try:
            return super().ask(model, prompt)
        except openai.APIConnectionError:
            raise SystemExit(
                "Can't reach Ollama at localhost:11434. Install it from https://ollama.com, "
                "then start the Ollama app (or run `ollama serve`)."
            )
        except openai.NotFoundError:
            raise SystemExit(f"Model '{model}' isn't downloaded yet. Run: ollama pull {model}")


PROVIDERS = {
    "gemini": Gemini,
    "claude": Claude,
    "openai": OpenAI,
    "ollama": Ollama,
}


# ---------------------------------------------------------------------------
# The bot itself: works the same for every provider
# ---------------------------------------------------------------------------


def generate_with_retry(provider, models, prompt):
    """Keep trying each model in turn until one returns a response. Ctrl+C to stop."""
    delay = FIRST_DELAY
    attempt = 1
    while True:
        for model in models:
            try:
                return model, provider.ask(model, prompt)
            except Exception as e:
                if not provider.is_temporary(e):
                    raise  # e.g. bad API key or unknown model — retrying won't help
                print(f"Attempt {attempt}: {model} unavailable ({type(e).__name__})")
                attempt += 1

        print(f"All models busy. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, MAX_DELAY)


def connect(provider_class):
    """Check the API key is set and create the provider's client."""
    api_key = None
    if provider_class.key_env:
        api_key = os.getenv(provider_class.key_env)
        if not api_key or api_key == "your-api-key-here":
            raise SystemExit(
                f"{provider_class.key_env} is not set. Add it to the .env file (see .env.example).\n"
                f"Get a key at {provider_class.key_url}"
            )
    try:
        return provider_class(api_key)
    except ImportError:
        raise SystemExit(
            f"The {provider_class.name} package isn't installed. Run: pip install {provider_class.package}"
        )


def list_providers():
    print("Providers (use with --provider):\n")
    for key, provider_class in PROVIDERS.items():
        needs = provider_class.key_env or "no API key"
        print(f"  {key:<7} {provider_class.name:<18} needs {needs}")
        print(f"          default models: {', '.join(provider_class.models)}\n")
    print("Use --model to try any other model the provider offers.")


def parse_args():
    parser = argparse.ArgumentParser(description="Say hello to the LLM of your choice.")
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        default=os.getenv("LLM_PROVIDER", "gemini").lower(),
        help="which LLM provider to use (default: gemini, or LLM_PROVIDER from .env)",
    )
    parser.add_argument("--model", help="a specific model name (default: the provider's usual models)")
    parser.add_argument("--prompt", default=PROMPT, help="what to ask the model")
    parser.add_argument("--list", action="store_true", help="show providers and their models, then exit")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.list:
        list_providers()
        return

    provider_class = PROVIDERS[args.provider]
    provider = connect(provider_class)

    # A model you pick yourself is tried on its own; otherwise use the provider's list
    models = [args.model] if args.model else provider_class.models

    model, reply = generate_with_retry(provider, models, args.prompt)

    print(f"Connected to {provider_class.name} successfully!\n")
    print(f"Model : {model}")
    print(f"Prompt: {args.prompt}\n")
    print("Response:")
    print(reply)


if __name__ == "__main__":
    main()
