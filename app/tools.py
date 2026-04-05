import os
from pathlib import Path
from app.config import logger, settings
from app.rag import get_context


def list_indexed_repos() -> str:

    # Returns a list of all repositories that have been indexed and are available for searching.
    # Use this tool first to see which projects you can discuss.

    registry_path = settings.repo_registry_path
    if not registry_path.exists():
        return "No repositories have been indexed yet."

    try:
        repos = registry_path.read_text().splitlines()
        repos = [r.strip() for r in repos if r.strip()]
        if not repos:
            return "The repository registry is empty."
        return "Available indexed repositories:\n" + "\n".join(f"- {r}" for r in repos)
    except Exception as e:
        logger.error(f"[TOOL ERROR] Failed to read registry: {e}")
        return "Error retrieving the list of repositories."


def get_file_content(repo_name: str, relative_path: str) -> str:

    # Retrieves the full text content of a specific file within a repository.
   # used to find a relevant file via search but need the full context (imports, class structure).
    # repos under /data/
    repo_root = settings.data_path / repo_name
    file_path = (repo_root / relative_path).resolve()

    try:
        if not str(file_path).startswith(str(repo_root.resolve())):
            logger.warning(f"[SECURITY] Attempted path traversal: {file_path}")
            return "Error: Access denied. Path is outside of repository boundaries."

        if not file_path.exists():
            return f"Error: File '{relative_path}' not found in repository '{repo_name}'."

        if not file_path.is_file():
            return f"Error: '{relative_path}' is a directory, not a file."

        content = file_path.read_text(encoding="utf-8", errors="replace")

        # long file limit
        if len(content) > 30000:
            content = content[:30000] + \
                "\n\n... [File truncated due to length] ..."

        return f"--- FULL CONTENT OF {relative_path} ---\n\n{content}"

    except Exception as e:
        logger.error(f"[TOOL ERROR] get_file_content failed: {e}")
        return f"Error reading file: {str(e)}"


def search_codebase(repo_name: str, query: str) -> str:

    # Searches the specified repository for code snippets related to the query.
    # Returns ranked chunks of code with file paths and metadata.

    logger.debug(f"[TOOL] Searching {repo_name} for: {query}")
    try:
        # Delegation to rag.py which already handles the hybrid search logic
        context = get_context(repo_name, query)
        return context
    except Exception as e:
        logger.exception(
            f"[TOOL ERROR] search_codebase failed for {repo_name}")
        return "Error performing search. Ensure the repo name is correct."


if __name__ == "__main__":
    print(search_codebase("test"))
