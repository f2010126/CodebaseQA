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

# default is the fake repo


def run_indexing(data_path="data/fake_repo_agent", save_path="vectorstore"):
    """
    FAISS index from a local repo directory.
    """

    try:
        logger.info(f"Loading documents from: {data_path}. Currently only .py")

        loader = DirectoryLoader(data_path, glob="**/*.py")
        docs = loader.load()

        if not docs:
            logger.warning("No documents found in data path.")
            return None

        logger.info(f"Loaded {len(docs)} documents")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )

        chunks = splitter.split_documents(docs)

        if not chunks:
            logger.warning("No chunks created from documents.")
            return None

        logger.info(f"Created {len(chunks)} chunks")

        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-2-preview"
            )
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise

        try:
            db = FAISS.from_documents(chunks, embeddings)
        except Exception as e:
            logger.error(f"FAISS index creation failed: {e}")
            raise

        try:
            db.save_local(save_path)
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            raise

        logger.info(f"Index saved at: {save_path}")
        return db

    except Exception as e:
        logger.exception(f"Indexing pipeline failed: {e}")
        raise


if __name__ == "__main__":
    run_indexing()
