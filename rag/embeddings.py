from __future__ import annotations

from langchain_openai import OpenAIEmbeddings


def make_embeddings(openai_api_key: str, model: str) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=model, openai_api_key=openai_api_key)

