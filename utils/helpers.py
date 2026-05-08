from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from utils.config import Settings


@lru_cache(maxsize=8)
def make_llm(model: str, api_key: str, temperature: float) -> ChatOpenAI:
    return ChatOpenAI(model=model, api_key=api_key, temperature=temperature)


def llm_from_settings(settings: Settings) -> ChatOpenAI:
    return make_llm(settings.openai_model, settings.openai_api_key, settings.openai_temperature)

