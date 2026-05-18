from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PLACEHOLDER_API_KEYS = frozenset(
    {
        "replace_me",
        "your-api-key-here",
        "your_openai_api_key",
        "sk-your-key-here",
        "changeme",
    }
)


def _validate_openai_api_key(key: str) -> None:
    lowered = key.strip().lower()
    if lowered in _PLACEHOLDER_API_KEYS:
        raise RuntimeError(
            "OPENAI_API_KEY is still a placeholder (e.g. REPLACE_ME). "
            "Edit `.env` in the project root and set a real key from "
            "https://platform.openai.com/account/api-keys"
        )
    if not key.startswith("sk-"):
        raise RuntimeError(
            "OPENAI_API_KEY does not look valid (expected to start with `sk-`). "
            "Check `.env` in the project root."
        )


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    tavily_api_key: str | None

    openai_model: str
    openai_temperature: float
    openai_embeddings_model: str

    sqlite_db_path: Path
    chroma_persist_dir: Path

    log_dir: Path
    log_level: str


def load_settings(env_file: str | os.PathLike[str] | None = None) -> Settings:
    """
    Loads configuration from environment variables.
    """
    dotenv_path = Path(env_file) if env_file else _PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=True)

    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise RuntimeError(
            f"Missing OPENAI_API_KEY. Create `{dotenv_path}` (see `.env.example`) and set your key."
        )
    _validate_openai_api_key(openai_api_key)

    tavily_api_key = os.getenv("TAVILY_API_KEY")
    tavily_api_key = tavily_api_key.strip() if tavily_api_key else None

    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    openai_embeddings_model = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small").strip()

    sqlite_db_path = Path(os.getenv("SQLITE_DB_PATH", "database/hotel.db"))
    chroma_persist_dir = Path(os.getenv("CHROMA_PERSIST_DIR", "rag/chroma"))

    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    return Settings(
        openai_api_key=openai_api_key,
        tavily_api_key=tavily_api_key,
        openai_model=openai_model,
        openai_temperature=openai_temperature,
        openai_embeddings_model=openai_embeddings_model,
        sqlite_db_path=sqlite_db_path,
        chroma_persist_dir=chroma_persist_dir,
        log_dir=log_dir,
        log_level=log_level,
    )

