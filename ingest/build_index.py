import logging
import shutil
from pathlib import Path
import pickle
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_community.document_loaders.blob_loaders import FileSystemBlobLoader
from langchain_community.retrievers import BM25Retriever

# Import the centralized settings and logger
from app.config import settings, logger


# default is the fake repo agent
REPO_REGISTRY_PATH = "data/repos.txt"  # Hard coded. Change it when possible


def register_repo(repo_name):
    """repo registration"""
    repo_path = settings.repo_registry_path
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    repos = set(repo_path.read_text().splitlines()
                ) if repo_path.exists() else set()
    repos.add(repo_name)

    repo_path.write_text("\n".join(sorted(filter(None, repos))) + "\n")


def get_embeddings_model():
    """ init model """
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview",
        google_api_key=settings.google_api_key
    )


def run_indexing(data_path: str = "data/fake_repo_agent"):
    # Indexing Pipeline
    source_dir = Path(data_path).resolve()  # enforcing absolute path
    repo_name = source_dir.name
    save_path = settings.vectorstore_root / repo_name

    # --- Clean-Slate Logic ---
    if save_path.exists():
        logger.info(
            f"Existing index found for {repo_name}. Wiping to prevent duplicates.")
        try:
            shutil.rmtree(save_path)
        except Exception as e:
            # No what? just append I guess
            logger.error(f"Failed to clear existing index: {e}")
    # create structure
    save_path.mkdir(parents=True, exist_ok=True)
    all_docs = []
    # load  glob and validation
    logger.info(f"Scanning {source_dir} for Python files...")
    # ensure glob or exclude patterns are tight to avoid .venv/ or __pycache__/
    # parser_threshold=500 means files smaller than 500 lines
    # get special AST treatment for splitting.
    py_loader = GenericLoader(
        blob_loader=FileSystemBlobLoader(str(source_dir), glob="**/*.py",
                                         suffixes=[".py"], show_progress=True),
        blob_parser=LanguageParser(
            language=Language.PYTHON, parser_threshold=500),
    )

    # loaders for text
    text_globs = ["README.md", "requirements.txt",
                  "pyproject.toml", "Dockerfile"]
    text_docs = []

    for glob_pattern in text_globs:
        try:
            loader = GenericLoader(
                blob_loader=FileSystemBlobLoader(
                    str(source_dir), glob=glob_pattern),
                blob_parser=LanguageParser(language=None)  # Plain text mode
            )
            text_docs.extend(loader.load())
        except:
            logger.warning(f"No files for pattern {glob_pattern}")

    try:
        all_docs = py_loader.load() + text_docs
        if not all_docs:
            logger.warning("No indexable files found.")
            return None
    except Exception as e:
        logger.error(f"Failed to load documents: {e}")
        return None

    # python-aware splitting
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=1500,  # for better code context
        chunk_overlap=200  # catch indentation/headers
    )

    chunks = splitter.split_documents(all_docs)
    for chunk in chunks:
        # LanguageParser adds "content_type" (e.g., 'function_definition')
        # and "source" to metadata automatically.
        # also enforce the absolute path
        chunk.metadata["repo"] = repo_name
        full_path = Path(chunk.metadata.get("source", "")).resolve()
        try:
            # calculates the path starting from the repo root (data_path)
            rel_path = full_path.relative_to(source_dir)
            chunk.metadata["source_file"] = str(rel_path)
        except ValueError:
            # Fallback
            chunk.metadata["source_file"] = full_path.name

    # vector mgmt
    embeddings = get_embeddings_model()

    try:
        # always create a NEW index
        logger.info(f"Creating fresh index for {repo_name}")
        db = FAISS.from_documents(chunks, embeddings)
        db.save_local(str(save_path))
        register_repo(repo_name)
        # adding exact keyword searching using BM25
        bm25_retriever = BM25Retriever.from_documents(chunks)
        with open(save_path / "bm25_retriever.pkl", "wb") as f:
            pickle.dump(bm25_retriever, f)
        logger.info(f"Hybrid indexing saved at: {save_path}")

        return db

    except Exception as e:
        logger.exception("Vector store operation failed")
        raise


if __name__ == "__main__":
    run_indexing()
