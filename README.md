# Webapp Chat Demo Ollama

A simple one-page Django clothing shop with a local Ollama-powered product advisor.

## Run

```bash
python -m pip install -r requirements.txt
python manage.py runserver
```

Open http://127.0.0.1:8000.

## Ollama

The chat endpoint calls Ollama's local API at:

```text
POST http://localhost:11434/api/chat
```

If `ollama` is not installed, install it first. On Linux, Ollama's official
installer is:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

By default the app uses `llama3.2`. Override these values as needed:

```bash
OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=llama3.2 python manage.py runserver
```

Make sure Ollama is running and the model is available locally. In one terminal,
start the Ollama server:

```bash
ollama serve
```

In another terminal, pull the model:

```bash
ollama pull llama3.2
```

In GitHub Codespaces, `localhost` means the codespace container, not your laptop.
Install and run Ollama inside the codespace, or point `OLLAMA_BASE_URL` at an
Ollama server the codespace can reach.
