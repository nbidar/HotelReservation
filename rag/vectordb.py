from __future__ import annotations

from pathlib import Path

import chromadb
from langchain_chroma import Chroma

from rag.embeddings import make_embeddings
from rag.rules import DEFAULT_COMPLIANCE_RULES


def ensure_compliance_collection(
    persist_dir: Path,
    openai_api_key: str,
    embeddings_model: str,
    collection_name: str = "compliance_rules",
) -> Chroma:
    """
    Creates/loads the compliance rules collection on disk and ensures at least one document exists.
    """
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    embeddings = make_embeddings(openai_api_key=openai_api_key, model=embeddings_model)

    vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )

    try:
        existing = vectorstore._collection.count()  # noqa: SLF001 (LangChain internal)
    except Exception:
        existing = 0

    if existing == 0:
        vectorstore.add_texts(
            texts=[DEFAULT_COMPLIANCE_RULES],
            ids=["compliance_rules"],
            metadatas=[{"source": "default_rules"}],
        )

    return vectorstore

