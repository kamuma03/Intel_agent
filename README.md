# Memory-Driven Customer Intelligence Agent

A "smart" AI assistant that remembers user interactions and facts using a persistent PostgreSQL memory layer. This agent can plug into various LLM providers (OpenAI, Claude, Gemini) and maintains context across sessions.

## Features

- **Persistent Memory**: Stores user interactions and specific facts (e.g., "My name is Alice") in a PostgreSQL database.
- **Context Awareness**: Retrieves recent conversation history and relevant facts to provide personalized responses.
- **Pluggable Architecture**: Easily switch between OpenAI, Anthropic, and Google Gemini models.
- **Automated Infrastructure**: Automatically manages a local PostgreSQL Docker container.
- **Secure**: Credentials managed via environment variables and masked in logs. DoS protection included.

## Prerequisites

- **Python 3.8+**
- **Docker** (must be running)

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

4.  **Configure Environment**:
    Copy the example environment file and edit it with your API keys.
    ```bash
    cp .env.example .env
    ```
    Open `.env` and add your API keys (e.g., `OPENAI_API_KEY`).

## Usage

Run the agent:

```bash
python main.py
```

The agent will automatically start the database container if it's not running.

### Commands

- **Chat**: Type directly to chat with the agent.
- **Save Facts**: `save <key> <value>` (e.g., `save name Alice` or `save hobby skiing`).
- **Exit**: Type `exit` or `quit`.

## Architecture

- `main.py`: Entry point. Orchestrates DB setup and runs the chat loop.
- `agent.py`: Core logic connecting Memory, LLM, and User.
- `memory.py`: Handles PostgreSQL interactions (storing/retrieving facts and logs).
- `db_manager.py`: Manages the Docker container lifecycle.
- `llm_providers.py`: Adapters for different AI models.

## Security

- **Credentials**: Stored in `.env`, never committed.
- **Logging**: Database passwords are masked in console output.
- **Validation**: User input is capped to prevent flooding.
