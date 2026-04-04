import logging
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# default is the fake repo agent

REPO_REGISTRY_PATH = "data/repos.txt"  # Hard coded. Change it when possible


def register_repo(repo_name):
    """Save to repos.txt, avoid duplicates"""
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(REPO_REGISTRY_PATH):
        with open(REPO_REGISTRY_PATH, "w") as f:
            f.write(repo_name + "\n")
        return

    with open(REPO_REGISTRY_PATH, "r+") as f:
        repos = {line.strip() for line in f.readlines()}
        if repo_name not in repos:
            f.write(repo_name + "\n")


def run_indexing(data_path="data/fake_repo_agent", save_path="vectorstore"):
    """
    FAISS index from a local repo directory.
    """
    try:
        logger.info(f"Loading documents from: {data_path}. Currently only .py")
        repo_name = os.path.basename(data_path)
        save_path = f"vectorestore/{repo_name}"
        logger.info(f"Indexing repo: {repo_name}")
        # load the repo. Currently only .py
        loader = DirectoryLoader(data_path, glob="**/*.py")
        docs = loader.load()

        if not docs:
            logger.warning("No documents found in data path.")
            return None

        logger.info(f"Loaded {len(docs)} documents")
        # added some metadata, might even add something for branches
        for doc in docs:
            doc.metadata["repo"] = repo_name

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )

        chunks = splitter.split_documents(docs)

        if not chunks:
            logger.warning("No chunks created from documents.")
            return None

        logger.info(f"Created {len(chunks)} chunks")

        # repo metadata persists after split
        for chunk in chunks:
            chunk.metadata["repo"] = repo_name

        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-2-preview"
            )
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise

        try:
            # append vector store or create new stuff
            if os.path.exists(save_path):
                logger.info("Loading existing vectorstore...")
                db = FAISS.load_local(
                    save_path,
                    embeddings,
                    allow_dangerous_deserialization=True)
                db.add_documents(chunks)
            else:
                # new
                logger.info("New vectorstore...")
                db = FAISS.from_documents(chunks, embeddings)
        except Exception as e:
            logger.error(f"FAISS index creation failed: {e}")
            raise

        try:
            db.save_local(save_path)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            raise
        register_repo(repo_name)
        logger.info(f"Index saved at: {save_path}")
        return db

    except Exception as e:
        logger.exception(f"Indexing pipeline failed: {e}")
        raise


if __name__ == "__main__":
    run_indexing()
