from app.agent import build_agent
from app.config import logger


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
    print("\n[System] Checking available repositories...")
    init_res = agent.invoke(
        {"input": "List the available repositories and introduce yourself."})
    print(f"\nAgent: {init_res.get('output')}")

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
            result = run_query(agent, query)

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
