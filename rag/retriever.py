from __future__ import annotations

from langchain_chroma import Chroma


def similarity_search(vectorstore: Chroma, query: str, k: int = 2) -> tuple[str, list]:
    docs = vectorstore.similarity_search(query, k=k)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}") for doc in docs
    )
    return serialized, docs

