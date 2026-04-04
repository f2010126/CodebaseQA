import logging
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# setting up in one place


class Settings(BaseSettings):
    google_api_key: str
    debug: bool = False
    repo_registry_path: Path = Path("data/repos.txt")
    vectorstore_root: Path = Path("vectorstore")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger(__name__)

# default is the fake repo agent

REPO_REGISTRY_PATH = "data/repos.txt"  # Hard coded. Change it when possible


def register_repo(repo_name):
    """repo registration"""
    settings.repo_registry_path.parent.mkdir(parents=True, exist_ok=True)

    existing_repos = set()
    if settings.repo_registry_path.exists():
        existing_repos = {
            line.strip() for line in settings.repo_registry_path.read_text().splitlines()}

    if repo_name not in existing_repos:
        with open(settings.repo_registry_path, "a") as f:
            f.write(f"{repo_name}\n")


def get_embeddings_model():
    """ init model """
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview",
        google_api_key=settings.google_api_key
    )


def run_indexing(data_path: str = "data/fake_repo_agent"):
    # Indexing Pipeline

    source_dir = Path(data_path)
    repo_name = source_dir.name
    save_path = settings.vectorstore_root / repo_name

    # load  glob and validation
    logger.info(f"Scanning {source_dir} for Python files...")
    loader = DirectoryLoader(str(source_dir), glob="**/*.py")

    try:
        docs = loader.load()
        if not docs:
            logger.warning(f"No .py files found in {source_dir}")
            return None
    except Exception as e:
        logger.error(f"Failed to load documents: {e}")
        return None

    # python-aware splitting
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(docs)
    for chunk in chunks:
        chunk.metadata["repo"] = repo_name
        # Add source path for easier debugging in the assistant
        chunk.metadata["source_file"] = Path(
            chunk.metadata.get("source", "")).name

    # 3. Vector Store Management
    embeddings = get_embeddings_model()

    try:
        if save_path.exists():
            logger.info(f"Updating existing index at {save_path}")
            db = FAISS.load_local(str(save_path), embeddings,
                                  allow_dangerous_deserialization=True)
            db.add_documents(chunks)
        else:
            logger.info(f"Creating new index for {repo_name}")
            db = FAISS.from_documents(chunks, embeddings)

        db.save_local(str(save_path))
        register_repo(repo_name)
        logger.info(f"Index saved at: {save_path}")
        return db

    except Exception as e:
        logger.exception("Vector store operation failed")
        raise


if __name__ == "__main__":
    run_indexing()
