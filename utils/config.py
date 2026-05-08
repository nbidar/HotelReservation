from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


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
    load_dotenv(dotenv_path=env_file, override=False)

    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise RuntimeError("Missing OPENAI_API_KEY. Add it to .env")

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

