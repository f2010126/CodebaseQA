# app/agent.py main one
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
    tool,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from app.config import logger
from app.tools import search_codebase, get_file_content, list_indexed_repos
from app.prompts import SYSTEM_PROMPT


def load_repos():
    path = "data/repos.txt"
    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        return [line.strip() for line in f.readlines()]

# Factory


def build_llm():
    try:
        # gemini-2.5-flash-lite is highly optimized for tool calling
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0
        )
    except Exception as e:
        logger.exception("Failed to initialize LLM")
        raise

# Builder


def build_agent() -> AgentExecutor:
    try:
        logger.info("Initializing Tool Calling Agent...")

        llm = build_llm()

        #  @tool decorator schemas used automatically
        tools = [search_codebase, get_file_content, list_indexed_repos]

        # ChatPromptTemplate for modern tool-calling support
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        #  tool calling agent
        agent = create_tool_calling_agent(llm, tools, prompt)

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

    except Exception as e:
        logger.exception("Agent initialization failed")
        raise
