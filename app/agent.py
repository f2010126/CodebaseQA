# app/agent.py main one
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.tools import Tool
from langsmith import Client
from app.config import logger
from app.tools import search_codebase


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
                description="""
Search the repository codebase for relevant files and code snippets.

Use this tool when the user asks about:
- code structure
- functions
- implementation details
- logging
- utilities
- debugging code

STRICT FORMAT RULES (VERY IMPORTANT):
- Action must be: search_codebase
- Action Input must be a plain string only
- DO NOT use function-call syntax

CORRECT:
Action: search_codebase
Action Input: logging

INCORRECT:
search_codebase(query="logging")
search_codebase("logging")
"""
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

        client = Client()
        prompt = client.pull_prompt("hwchase17/react")

        agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
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
