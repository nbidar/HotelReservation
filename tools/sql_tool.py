from __future__ import annotations

from pathlib import Path

from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI


def make_sql_tools(db_path: Path, llm: ChatOpenAI):
    db = SQLDatabase.from_uri(f"sqlite:///{db_path.as_posix()}")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    return toolkit.get_tools()

