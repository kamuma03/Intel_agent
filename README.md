# Memory-Driven Customer Intelligence Agent (LangChain RAG)

A smart AI assistant that uses a **Dual-Layer Memory** system to provide personalized responses. It combines **Short-Term Memory** (conversation context) with **Long-Term Memory** (vector store + structured preferences) to remember user facts across sessions.

Powered by **LangChain**, **Chroma**, **SQLite**, and **Ollama Embeddings** (`nomic-embed-text`).

---

## Features

- **Dual-Layer Memory**:
  - **Vector Store (Chroma)**: Semantic search for past interactions.
  - **Structured DB (SQLite)**: Specific user preferences and facts.
  - **Conversation Summary**: Maintains recent chat context.
- **Multi-Provider Support**:
  - **Ollama** (default): Run locally with models like `qwen2.5` or `llama3`.
  - **OpenAI**: GPT-4o.
  - **Anthropic**: Claude 3.5 Sonnet.
  - **Google**: Gemini 2.0 Flash.
- **No Docker Required**: Runs entirely in your local Python environment.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CustomerIntelligenceAgent                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Short-Term     │  │   Long-Term      │  │   Structured     │  │
│  │   Memory         │  │   Memory         │  │   Memory         │  │
│  │   (LangChain)    │  │   (Chroma)       │  │   (SQLite)       │  │
│  │                  │  │                  │  │                  │  │
│  │  Conversation    │  │  Semantic Search │  │  Known Facts     │  │
│  │  Summary         │  │  of Past Chats   │  │  & Preferences   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│                          ┌───────────────────────────────────────┐     │
│                          │       LLM Backend (Pluggable)         │     │
│                          │  Ollama | OpenAI | Anthropic | Google │     │
│                          └───────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

### Files
| File | Description |
|------|-------------|
| `agent.py` | Core `CustomerIntelligenceAgent` class with memory and RAG logic. |
| `main.py` | CLI entry point for interactive chat. |
| `memory_db/` | Chroma vector store persistence directory. |
| `user_<id>.db` | SQLite file for structured preferences. |

---

## Prerequisites

- **Python 3.10+**
- **Ollama** (required for local LLM and embeddings)
  - Pull the embedding model: `ollama pull nomic-embed-text`
  - Pull a chat model: `ollama pull qwen2.5:32b` (or your preferred model)
- **API Keys** (optional, depending on provider):
  - `OPENAI_API_KEY` (if using OpenAI)
  - `ANTHROPIC_API_KEY` (if using Claude)
  - `GOOGLE_API_KEY` (if using Gemini)

---

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd Intel_agent
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start Ollama** (for default local mode):
    ```bash
    ollama serve
    ```

5.  **Configure Environment** (optional, for cloud providers):
    Create a `.env` file if using OpenAI, Anthropic, or Google:
    ```bash
    cp .env.example .env
    ```
    Edit `.env`:
    ```env
    # Only needed if using cloud providers:
    # OPENAI_API_KEY=sk-...
    # ANTHROPIC_API_KEY=sk-ant-...
    # GOOGLE_API_KEY=...
    # LLM_PROVIDER=openai  # Optional: defaults to ollama
    ```

---

## Usage

Run the agent:

```bash
python main.py
```

### Switching Providers

The agent defaults to **Ollama**. Set `LLM_PROVIDER` to switch:

| Provider | Command |
|----------|---------|
| Ollama (default) | `python main.py` |
| OpenAI | `LLM_PROVIDER=openai python main.py` |
| Anthropic (Claude) | `LLM_PROVIDER=anthropic python main.py` |
| Google (Gemini) | `LLM_PROVIDER=google python main.py` |

### CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `<message>` | Chat with the agent | `What is my favorite hobby?` |
| `save <key> <value> <category>` | Save a preference | `save hobby skiing personal` |
| `exit` / `quit` | Exit the application | `exit` |

---

## Example Session

```
=== Memory-Driven Customer Intelligence Agent (LangChain RAG) ===
Initializing agent with provider: ollama

Agent Ready! (User ID: user_123)
Type 'exit' to quit. Type 'save <key> <value> <category>' to save a preference manually.

You: save hobby skiing personal
Saved preference: hobby=skiing (personal)

You: What do I like to do?
Agent: Based on my records, you enjoy skiing! Is there anything else you'd like to share?

You: exit
Goodbye!
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in your `.venv`. |
| `Ollama connection refused` | Ensure Ollama is running (`ollama serve`). |
| `Embedding model not found` | Pull the model: `ollama pull nomic-embed-text` |
| `OPENAI_API_KEY not found` | Only needed if using `LLM_PROVIDER=openai`. |
| `ANTHROPIC_API_KEY not found` | Ensure `.env` file has `ANTHROPIC_API_KEY=sk-ant-...` |
| `GOOGLE_API_KEY not found` | Ensure `.env` file has `GOOGLE_API_KEY=...` |
| Permission denied on `memory_db` | Delete the folder: `rm -rf memory_db` and restart. |

---

## License

This project is licensed under the GPL-3.0 License.
