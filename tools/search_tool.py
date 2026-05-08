from __future__ import annotations

from langchain_tavily import TavilySearch


def make_tavily_search_tool(tavily_api_key: str, max_results: int = 5, topic: str = "general") -> TavilySearch:
    return TavilySearch(max_results=max_results, topic=topic, tavily_api_key=tavily_api_key)

