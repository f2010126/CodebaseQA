# Handles the retrival stuff
from langchain_community.vectorstores import FAISS
# FAISS (Facebook AI Similarity Search) is an open-source library by Meta
# for efficient, high-performance similarity search and clustering of dense, high-dimensional vectors.
# using it for semantic search
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import pickle
from langchain_classic.retrievers import EnsembleRetriever
from app.config import logger, settings

BM25_K = 2
FAISS_K = 2


def load_hybrid_retriever(repo_name: str):
    save_path = settings.vectorstore_root / repo_name

    if not save_path.exists():
        logger.error(f"vectorstore directory missing for repo: {repo_name}")
        return None

    try:
        #  for vector embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2-preview",
            google_api_key=settings.google_api_key
        )
        # check if the index is there
        if not (save_path / "index.faiss").exists():
            logger.error(f"FAISS index files missing in {save_path}")
            return None

        vector_db = FAISS.load_local(
            str(save_path),
            embeddings,
            allow_dangerous_deserialization=True  # controversial
        )
        vector_retriever = vector_db.as_retriever(search_kwargs={"k": FAISS_K})

        # keyword search (BM25)
        bm25_path = save_path / "bm25_retriever.pkl"
        bm25_retriever = None

        if bm25_path.exists():
            try:
                with open(bm25_path, "rb") as f:
                    bm25_retriever = pickle.load(f)
                    bm25_retriever.k = BM25_K
            except (pickle.UnpicklingError, EOFError) as e:
                logger.warning(
                    f"BM25 index corrupted for {repo_name}: {e}. Using Vector-only.")
        else:
            logger.warning(
                f"BM25 index not found for {repo_name}. Using Vector-only.")

        # 3. Hybrid Ensemble (RRF Merging)
        if bm25_retriever:
            return EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                # Eh equal importance. Have to think about this one
                weights=[0.5, 0.5]
            )
        return vector_retriever  # Fallback

    except Exception as e:
        logger.error(f"Hybrid retrieval load failed: {e}")
        raise

# Entry point to LLM


def get_context(repo_name: str, query: str) -> str:
    retriever = load_hybrid_retriever(repo_name)
    if not retriever:
        return "No context found."

    docs = retriever.invoke(query)
    # Trying to avoid confusion with "deduplication" logic and labelled chunks
    context_parts = []
    seen_files = set()  # track files for repeats

    context_parts = []
    for doc in docs:
        source = doc.metadata.get('source_file', 'unknown')
        # Content type helps the agent know if it's looking at a function or a class
        ctype = doc.metadata.get('content_type', 'code')
        # We saw this already.
        prefix = "CONTINUED: " if source in seen_files else ""
        seen_files.add(source)

        context_parts.append(
            f"--- {prefix}FILE: {source} ({ctype}) ---\n{doc.page_content}")

    # return stuff thats more unique to avoid stuffing the model up. Mind you, this is because the model is a bit smaller
    return "\n\n".join(context_parts)
