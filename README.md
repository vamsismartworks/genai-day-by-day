# GenAI Day by Day

A small step forward in Generative AI each day. Use the LLM you like: Google Gemini,
Anthropic Claude, OpenAI GPT, or a free local model through Ollama.
Each day lives in its own folder and builds on the previous one.

## Progress

| Day | Topic | Folder | Status |
|-----|-------|--------|--------|
| 01 | Connect to Gemini and get a response (`hello_bot.py`) | `week-01-chat-with-LLM/` | ✅ |
| 01+ | Same bot, but pick any LLM: Gemini, Claude, OpenAI or Ollama (`hello_bots.py`) | `week-01-chat-with-LLM/` | ✅ |
| 02 | A web page to chat with Gemini, built with FastAPI (`main.py`) | `week-02-add-chat-interface/` | ✅ |

## Setup (one time)

A virtual environment (`.venv/`) is a private folder of Python packages for this
project, so the packages installed here don't clash with the rest of your system.

### 1. Go to the project folder

```bash
cd ~/Learning_AI/genai-day-by-day
```

### 2. Create the virtual environment

```bash
python3 -m venv .venv
```

This creates a `.venv/` folder. You only do this once.
Don't have to create virtual environment everytime. (`.venv/` is git-ignored.)

### 3. Activate it

```bash
source .venv/bin/activate
```

Your prompt should now start with `(.venv)`. To confirm, run:

```bash
which python        # should end in genai-day-by-day/.venv/bin/python
```

### 4. Install the packages

```bash
pip install -r requirements.txt
```

This installs `python-dotenv` and the SDKs for every provider (`google-genai`, `anthropic`,
`openai`) into `.venv/` only. Each provider's SDK is loaded only when you use it.

### 5. Add your API key

```bash
cp .env.example .env
```

Open `.env` and replace `your-api-key-here` with the key for **at least one** provider:

| Provider | `--provider` | Key in `.env` | Get a key |
|----------|--------------|---------------|-----------|
| Google Gemini (free tier) | `gemini` | `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| Anthropic Claude | `claude` | `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys |
| OpenAI GPT | `openai` | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Ollama (local, free) | `ollama` | none | Install from https://ollama.com, then `ollama pull llama3.2:3b` |

`hello_bot.py` only needs `GEMINI_API_KEY`. For `hello_bots.py`, set `LLM_PROVIDER` in `.env` to choose
the provider used when you don't pass `--provider`.
`.env` is git-ignored, so your key stays out of version control.

## Run a day

Each time you open a new terminal, activate the environment first, then run the script
from the project root:

```bash
cd ~/Learning_AI/genai-day-by-day
source .venv/bin/activate
python week-01-chat-with-LLM/hello_bot.py
```

`hello_bot.py` is the simple, Gemini-only version. To use a different LLM, run
`hello_bots.py` and choose a provider and model with flags:

```bash
python week-01-chat-with-LLM/hello_bots.py --provider claude
python week-01-chat-with-LLM/hello_bots.py --provider openai --model gpt-5.4-nano
python week-01-chat-with-LLM/hello_bots.py --provider ollama --prompt "Tell me a joke"
python week-01-chat-with-LLM/hello_bots.py --list
```

### Week 02: the web page

```bash
cd week-02-add-chat-interface
uvicorn main:app --reload --port 8000
```

`main:app` means "the `app` object in `main.py`", so run it from inside `week-02-add-chat-interface/`.
`--reload` restarts the server whenever you save a change to the code.

Then open http://127.0.0.1:8000 in your browser, type a prompt, pick a Gemini model and click
**Ask Gemini**. Press `Ctrl+C` in the terminal to stop the server, then `cd ..` to go back to the project root.

How it fits together:

- `week-02-add-chat-interface/main.py` is the **server**, built with [FastAPI](https://fastapi.tiangolo.com).
  It serves the page and is the only part that talks to Gemini, so your API key never
  reaches the browser.
- `week-02-add-chat-interface/static/index.html` is the **page**. When you click the button, its JavaScript
  sends your prompt to the server (`POST /api/ask`) and shows the reply.
- FastAPI also writes interactive API docs for you: open http://127.0.0.1:8000/docs to
  call `/api/ask` directly, without the page.

Or skip activation and call the environment's Python directly:

```bash
.venv/bin/python week-01-chat-with-LLM/hello_bot.py
```

When you're done, leave the environment with:

```bash
deactivate
```

**VS Code:** open the Command Palette (`Cmd+Shift+P`) → **Python: Select Interpreter** →
pick the one in `./.venv`. The Run button and new terminals will then use it automatically.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'dotenv'` (or `google`) | Running with the system Python, not the venv | `source .venv/bin/activate`, then `pip install -r requirements.txt` |
| `zsh: command not found: python` | The venv isn't active (macOS only has `python3`) | Activate the venv, or use `.venv/bin/python` |
| `GEMINI_API_KEY is not set` (or `ANTHROPIC_…`/`OPENAI_…`) | `.env` missing or still has the placeholder | Copy `.env.example` to `.env` and paste your key |
| `The ... package isn't installed` | That provider's SDK is missing | `pip install -r requirements.txt` |
| `Can't reach Ollama at localhost:11434` | Ollama isn't running | Start the Ollama app, or run `ollama serve` |
| `Model '...' isn't downloaded yet` | Ollama doesn't have that model | `ollama pull <model>` |
| `404 NOT_FOUND ... model ... is no longer available` | The provider retired that model | Pass a current one with `--model` (`hello_bots.py`), or update the model list in the script |
| `503 UNAVAILABLE ... high demand` | The provider is temporarily overloaded | The script retries by itself; press Ctrl+C to stop |
| `address already in use` (port 8000) | The web page server is already running in another terminal | Stop it with `Ctrl+C` there, or close that terminal |
