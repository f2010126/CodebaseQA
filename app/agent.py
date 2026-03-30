# app/agent.py main one
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.tools import Tool

from app.config import logger
from app.tools import search_codebase
from app.prompts import SYSTEM_PROMPT


# Factory
def build_llm():
    try:
        logger.info("Initializing LLM (Gemini)...")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0
        )

        logger.info("LLM initialized successfully")
        return llm

    except Exception as e:
        logger.exception("Failed to initialize LLM")
        raise


# Tools
def build_tools():
    try:
        logger.info("Building tools...")

        tools = [
            Tool(
                name="search_codebase",
                func=search_codebase,
                description="Search the codebase for relevant files and code snippets"
            )
        ]

        logger.info(f"{len(tools)} tool(s) registered successfully")
        return tools

    except Exception as e:
        logger.exception("Failed to build tools")
        raise


# Builder
def build_agent() -> AgentExecutor:
    """
    combine the functions
    """

    try:
        logger.info("Starting agent initialization pipeline...")

        llm = build_llm()
        tools = build_tools()

        logger.info("Creating ReAct agent...")

        agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=SYSTEM_PROMPT
        )

        logger.info("Wrapping agent in AgentExecutor...")

        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True
        )

        logger.info("Agent initialized successfully")
        return executor

    except Exception as e:
        logger.exception("Agent initialization failed")
        raise
