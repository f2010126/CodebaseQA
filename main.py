from app.agent import build_agent
from app.config import logger


def get_agent():
    return build_agent()


def run_query(agent, query: str):
    logger.debug(f"[USER QUERY] {query}")
    return agent.invoke({"input": query})


def start_agent():
    agent = get_agent()

    while True:
        try:
            query = input("\nAsk about codebase: ")

            if query.lower() in ["exit", "quit"]:
                break

            result = run_query(agent, query)

            print("\n--- ANSWER ---\n")
            print(result.get("output", "No output returned"))

        except KeyboardInterrupt:
            print("\nExiting...")
            break

        except Exception as e:
            logger.error(f"[RUNTIME ERROR] {e}")
            print("Something went wrong. Check logs.")


if __name__ == "__main__":
    start_agent()
