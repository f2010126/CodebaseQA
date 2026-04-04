from app.rag import get_retriever
from app.config import logger


def search_codebase(query: str) -> str:
    logger.debug(f"[TOOL] search_codebase called with query: {query}")

    try:
        retriever = get_retriever()
        docs = retriever.invoke(query)

        if not docs:
            logger.warning(f"[TOOL] No documents retrieved for query: {query}")
            return "No relevant code found."

        formatted_chunks = []

        for doc in docs:
            source = doc.metadata.get("source", "unknown")
            repo = doc.metadata.get("repo", "unknown")  # use metadata

            formatted_chunks.append(
                f"REPO: {repo}\n"
                f"FILE: {source}\n"
                f"CODE:\n{doc.page_content}\n"
                f"{'-' * 40}"
            )

        result = "\n\n".join(formatted_chunks)

        logger.debug(
            f"[TOOL] Retrieved {len(docs)} documents for query: {query}"
        )
        return result

    except Exception as e:
        logger.exception("[TOOL ERROR] search_codebase failed")
        return "Error retrieving codebase."


if __name__ == "__main__":
    print(search_codebase("test"))
