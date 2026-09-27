# GenAI Day by Day

A small step forward in Generative AI each day, using Google's Gemini models.
Each day lives in its own folder and builds on the previous one.

## Progress

| Day | Topic | Folder | Status |
|-----|-------|--------|--------|
| 01 | Connect to Gemini with an API key and get a response | `day01-hello-bot/` | ⬜ |

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

This creates a `.venv/` folder. You only do this once. (`.venv/` is git-ignored.)

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

This installs `google-genai` and `python-dotenv` into `.venv/` only.

### 5. Add your API key

```bash
cp .env.example .env
```

Open `.env` and replace `your-api-key-here` with your key.
Get a free API key at https://aistudio.google.com/apikey.
`.env` is git-ignored, so your key stays out of version control.

## Run a day

Each time you open a new terminal, activate the environment first, then run the script
from the project root:

```bash
cd ~/Learning_AI/genai-day-by-day
source .venv/bin/activate
python day01-hello-bot/hello_bot.py
```

Or skip activation and call the environment's Python directly:

```bash
.venv/bin/python day01-hello-bot/hello_bot.py
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
| `GEMINI_API_KEY is not set` | `.env` missing or still has the placeholder | Copy `.env.example` to `.env` and paste your key |
| `404 NOT_FOUND ... model ... is no longer available` | Google retired that model | Replace that name in the `MODELS` list in the script with the model the error message suggests |
| `503 UNAVAILABLE ... high demand` | Gemini is temporarily overloaded | The script retries automatically (switching to the lighter model too) until it gets a response; press `Ctrl+C` to stop |
