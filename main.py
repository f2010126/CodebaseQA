from app.agent import build_agent, chat_history_store
from app.config import logger
import langchain
langchain.debug = True


def get_agent():
    # Tool calling one now
    return build_agent()


def run_query(agent, query: str):
    logger.debug(f"[USER QUERY] {query}")
   # format for tool calling
    return agent.invoke({"input": query})


def start_agent():
    print("--- Codebase Assistant Initializing ---")
    agent = get_agent()
    # define a constant session ID for this CLI run TODO: add a config
    session_config = {"configurable": {"session_id": "cli_session"}}
    print("\n[System] Checking available repositories...")
    try:
        init_res = agent.invoke(
            {"input": "List the available repositories and introduce yourself."},
            config=session_config
        )
        print(f"\nAgent: {init_res.get('output')}")
        chat_history_store["cli_session"].clear()
        logger.info("Startup handshake cleared from memory.")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")

    print("System ready. Type 'exit' to quit.")
    while True:
        try:
            query = input("\nAsk about codebase: ")

            if not query.strip():
                continue

            if query.lower() in ["exit", "quit"]:
                break

            # The invocation remains the same, but the internal
            # 'verbose=True' in AgentExecutor will show the JSON tool calls.
            result = agent.invoke({"input": query},
                                  config=session_config  # use the history
                                  )
            # Debugging
            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    print(f"Tool Used: {action.tool}")
            print("\n--- ANSWER ---\n")
            print(result.get("output", "No output returned"))

        except KeyboardInterrupt:
            print("\nExiting...")
            break

        except Exception as e:
            logger.exception(f"[RUNTIME ERROR] {e}")
            print(f"An error occurred: {e}. Check logs for details.")


if __name__ == "__main__":
    start_agent()
