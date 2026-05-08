from __future__ import annotations

from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.compliance_agent import compliance_generate_node, compliance_node, make_retrieve_tool
from agents.conversation_agent import conversation_node
from agents.error_handler_agent import (
    alternative_model_node,
    degraded_functionality_node,
    error_handler_node,
    human_intervention_node,
)
from agents.reservation_agent import reservation_node
from agents.sentiment_agent import get_sentiment, sentiment_node
from agents.web_search_agent import web_search_node
from database.db import init_db
from rag.rules import DEFAULT_COMPLIANCE_RULES
from rag.vectordb import ensure_compliance_collection
from tools.search_tool import make_tavily_search_tool
from tools.sql_tool import make_sql_tools
from utils.helpers import make_llm
from workflows.routing import choose_error_recovery, choose_next_node
from workflows.state import AppState


def build_graph(*, settings, logger):
    """
    Builds the full LangGraph orchestration described across the notebooks:
    - Sentiment -> tools -> Conversation router
    - Compliance (RAG) gated flow
    - Reservation agent with SQL tools
    - Web search agent with Tavily tool
    - Central error handling + recovery routing
    - MemorySaver checkpointer for session/thread persistence
    """
    # Storage
    init_db(settings.sqlite_db_path, seed=True)

    vectorstore = ensure_compliance_collection(
        persist_dir=settings.chroma_persist_dir,
        openai_api_key=settings.openai_api_key,
        embeddings_model=settings.openai_embeddings_model,
    )
    retrieve_tool = make_retrieve_tool(vectorstore)

    # LLMs
    llm = make_llm(settings.openai_model, settings.openai_api_key, settings.openai_temperature)
    llm_fallback = make_llm("gpt-4o", settings.openai_api_key, settings.openai_temperature)

    # Tools
    sql_tools = make_sql_tools(settings.sqlite_db_path, llm=llm)
    rag_tools = [retrieve_tool]
    sentiment_tools = [get_sentiment]

    search_tools = []
    if settings.tavily_api_key:
        search_tools = [make_tavily_search_tool(settings.tavily_api_key)]

    llm_with_sql_tools = llm.bind_tools(tools=sql_tools)
    llm_with_rag_tools = llm.bind_tools(tools=rag_tools)
    llm_with_sentiment_tools = llm.bind_tools(tools=sentiment_tools)
    llm_with_search_tools = llm.bind_tools(tools=search_tools) if search_tools else llm

    memory = MemorySaver()

    builder = StateGraph(AppState)

    # Nodes
    builder.add_node("sentiment_analysis", lambda s: sentiment_node(s, llm_with_sentiment_tools))
    builder.add_node("conv_assistant", lambda s: conversation_node(s, llm))
    builder.add_node("reservation_assistant", lambda s: reservation_node(s, llm, llm_with_sql_tools))
    builder.add_node("compliance_checker", lambda s: compliance_node(s, llm_with_rag_tools, DEFAULT_COMPLIANCE_RULES))
    builder.add_node("web_search_assistant", lambda s: web_search_node(s, llm_with_search_tools))

    # Tool nodes
    builder.add_node("sentiment_tools", ToolNode(sentiment_tools))
    builder.add_node("sql_tools", ToolNode(sql_tools))
    builder.add_node("rag_tools", ToolNode(rag_tools))
    if search_tools:
        builder.add_node("search_tools", ToolNode(search_tools))

    builder.add_node("retriever", lambda s: compliance_generate_node(s, llm, DEFAULT_COMPLIANCE_RULES))

    # Error nodes
    builder.add_node("error_handler", lambda s: error_handler_node(s, logger))
    builder.add_node("human_intervention", lambda s: human_intervention_node(s, llm_fallback))
    builder.add_node("alternative_model", lambda s: alternative_model_node(s, llm_fallback))
    builder.add_node("degraded_functionality_retrieval", degraded_functionality_node)

    # Edges
    builder.add_edge(START, "sentiment_analysis")

    builder.add_conditional_edges(
        "sentiment_analysis",
        tools_condition,
        path_map={"tools": "sentiment_tools", "__end__": "conv_assistant"},
    )
    builder.add_edge("sentiment_tools", "sentiment_analysis")

    builder.add_conditional_edges(
        "conv_assistant",
        choose_next_node,
        path_map=["reservation_assistant", "compliance_checker", "web_search_assistant", "error_handler", "__end__"],
    )

    builder.add_conditional_edges(
        "reservation_assistant",
        tools_condition,
        path_map={"tools": "sql_tools", "__end__": "__end__"},
    )
    builder.add_edge("sql_tools", "reservation_assistant")

    builder.add_conditional_edges(
        "compliance_checker",
        tools_condition,
        path_map={"tools": "rag_tools", "__end__": "conv_assistant"},
    )
    builder.add_edge("rag_tools", "retriever")
    builder.add_edge("retriever", "conv_assistant")

    if search_tools:
        builder.add_conditional_edges(
            "web_search_assistant",
            tools_condition,
            path_map={"tools": "search_tools", "__end__": "__end__"},
        )
        builder.add_edge("search_tools", "web_search_assistant")
    else:
        # Without a web search tool configured, just end.
        builder.add_edge("web_search_assistant", "__end__")

    # Error recovery routing
    builder.add_conditional_edges(
        "error_handler",
        choose_error_recovery,
        path_map=["alternative_model", "degraded_functionality_retrieval", "human_intervention"],
    )
    builder.add_edge("human_intervention", "__end__")
    builder.add_conditional_edges(
        "alternative_model",
        choose_next_node,
        path_map=["reservation_assistant", "compliance_checker", "web_search_assistant", "error_handler", "__end__"],
    )

    return builder.compile(checkpointer=memory)

