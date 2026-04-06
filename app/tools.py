from app.config import logger, settings
from app.rag import get_context
from langchain_core.tools import tool
from pathlib import Path


@tool
def list_indexed_repos() -> str:
    """
    List all repositories that have been indexed and are available for searching.
    Always call this tool first if you are unsure which repositories are available.
    """

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


@tool
def get_file_content(repo_name: str, relative_path: str) -> str:
    """
    Read the full text of a specific file. 
    Use this when search_codebase finds a relevant file but the snippet is too short 
    to understand the full logic, imports, or class structure.
    - repo_name: The name of the repository.
    - relative_path: The path to the file (e.g., 'src/utils.py') found in search results.
    """
    repo_root = (settings.data_path / repo_name).resolve()
    file_path = (repo_root / relative_path).resolve()

    # path is inside the repo data directory
    if not str(file_path).startswith(str(repo_root)):
        logger.warning(
            f"Security: Blocked path traversal attempt to {file_path}")
        return "Error: Access denied. Path is outside repository boundaries."

    if not file_path.exists() or not file_path.is_file():
        # No need for an error log here, just a debug or info log
        logger.info(f"File not found: {relative_path} in {repo_name}")
        return f"Error: File '{relative_path}' not found."

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        if len(content) > 30000:  # extreme cases
            content = content[:30000] + "\n... [File Truncated] ..."
        return f"--- CONTENT OF {relative_path} ---\n\n{content}"
    except Exception as e:
        # How to fix??
        logger.exception(f"Failed to read file {relative_path}")
        return f"Error reading file: {str(e)}"


@tool
def search_codebase(repo_name: str, query: str) -> str:
    """
    Search a specific repository for code snippets and logic related to a query.
    - repo_name: The exact name of the repository to search (use list_indexed_repos to find names).
    - query: The technical term, function name, or concept you are looking for.
    """
    # Prevent firing empty queries.
    if not query or not query.strip():
        logger.warning(f"[TOOL] Empty query blocked for repo: {repo_name}")
        return "Error: Query was empty. Please provide technical keywords to search for."

    logger.debug(f"[TOOL] Searching {repo_name} for: {query}")
    try:
        # Delegation to rag.py
        context = get_context(repo_name, query)
        return context
    except Exception as e:
        logger.exception(
            f"[TOOL ERROR] search_codebase failed for {repo_name}")
        return f"Error performing search: {str(e)}"


if __name__ == "__main__":
    print(search_codebase("test"))
