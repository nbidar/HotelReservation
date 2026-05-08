# AI-Powered Multi-Agent Hotel Customer Support (Streamlit)

This repository is a production-style refactor of the original notebook-based **AI-Powered Multi-Agent Hotel Customer Support System** into a modular Python + **Streamlit** application powered by **LangGraph**.

## Features preserved from notebooks

- **LangGraph orchestration** (routing + tool nodes)
- **Conversation Coordinator agent**
- **Reservation / SQL agent** (SQLite + LangChain SQL toolkit tools)
- **Compliance / RAG agent** (ChromaDB + embeddings + retrieval tool)
- **Sentiment Analysis agent** (TextBlob + tool)
- **Web Search agent** (Tavily Search tool)
- **Centralized error handling + recovery routes** (fallback model + degraded retrieval path)

## Folder structure

- `app.py`: Streamlit entrypoint
- `agents/`: each agent node implementation
- `workflows/`: LangGraph `State`, routing, and graph builder
- `database/`: SQLite init + query definitions
- `rag/`: embeddings, Chroma persistence, retriever, and default compliance rules
- `tools/`: Tavily / SQL toolkit / translation tooling
- `ui/`: Streamlit UI helpers (sidebar, chat UI, CSS components)
- `utils/`: config + logger + shared prompts
- `logs/`: runtime logs (created automatically)

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file (recommended) by copying the template:

```bash
copy .env.example .env
```

4. Fill in at least:
- `OPENAI_API_KEY`
- `TAVILY_API_KEY` (optional but required for web search)

5. (One-time) download TextBlob corpora:

```bash
python -m textblob.download_corpora
```

## Run the app

```bash
streamlit run app.py
```

## Execution flow (high level)

1. **Sentiment agent** runs first (translates to English for sentiment if needed).
2. **Conversation coordinator** produces either:
   - a direct response, or
   - a routing marker: `reservation_assistant`, `compliance_checker`, `web_search_assistant`
3. Routed agents run with **tool nodes**:
   - Reservation → SQL tools
   - Compliance → RAG retrieval tool → back to conversation
   - Web search → Tavily tool
4. If any node sets an error, flow routes to the **error handler**, which chooses a recovery strategy.

## How agents communicate

All agents communicate through a shared LangGraph **state** (`workflows/state.py`) carrying:
- `messages` (LangChain messages, persisted via `MemorySaver`)
- `confidence`, `sentiment`, `language`
- error metadata and UI artifacts

## Deploy to EC2 (quick guide)

- **Instance**: start with `t3.large` (Transformers models + Chroma can be memory-heavy).
- **OS**: Ubuntu 22.04+
- **Install**: Python 3.11, `pip`, and system deps for `torch` if needed.
- **Run**:
  - Use `tmux`/`screen` for quick tests, or
  - Use `systemd` (recommended) or Docker for production.
- **Reverse proxy**: Nginx → Streamlit (port 8501).
- **Secrets**: store `.env` via SSM Parameter Store / Secrets Manager instead of committing.

## Scaling later

- **State store**: replace `MemorySaver` with a persistent checkpointer (Redis/Postgres) per LangGraph best practices.
- **Async + streaming**: enable true token streaming in LangChain callbacks and use `st.write_stream`.
- **Vector DB**: move Chroma to a managed vector DB if needed (or run Chroma server).
- **Database**: move SQLite → Postgres for concurrency and transactional guarantees.
- **Observability**: export structured logs + traces (OpenTelemetry).

