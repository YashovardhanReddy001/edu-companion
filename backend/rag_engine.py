from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHROMA_PERSIST_DIR = "./chroma_db"


class _ChromaWrapper:
    """A minimal wrapper around chromadb Collection to provide the
    `add_documents` and `similarity_search` methods expected by the rest
    of the code. Uses sentence-transformers directly for embeddings."""

    def __init__(self, collection, embed_model):
        self._col = collection
        self._model = embed_model

    def add_documents(self, docs):
        from uuid import uuid4

        texts = [getattr(d, "page_content", str(d)) for d in docs]
        metadatas = [getattr(d, "metadata", {}) for d in docs]
        ids = [str(uuid4()) for _ in texts]
        embeddings = self._model.encode(texts, show_progress_bar=False).tolist()
        self._col.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    def similarity_search(self, query, k=3):
        from types import SimpleNamespace

        q_emb = self._model.encode([query], show_progress_bar=False)[0].tolist()
        res = self._col.query(query_embeddings=[q_emb], n_results=k, include=["documents", "metadatas"])
        docs = []
        for doc_text, meta in zip(res.get("documents", [[]])[0], res.get("metadatas", [[]])[0]):
            docs.append(SimpleNamespace(page_content=doc_text, metadata=meta))
        return docs


_VECTOR_STORE = None


def get_vector_store():
    """Return a persistent Chromadb-backed store wrapped to match the
    minimal interface used in this project. Initializes the sentence-transformers
    model on first call."""
    global _VECTOR_STORE
    if _VECTOR_STORE is not None:
        return _VECTOR_STORE

    try:
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError(f"Missing dependency for vector store: {e}")

    try:
        client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_PERSIST_DIR))
    except Exception:
        client = chromadb.Client()

    collection = client.get_or_create_collection(name="edu_companion_docs")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    _VECTOR_STORE = _ChromaWrapper(collection, model)
    return _VECTOR_STORE

def process_and_store_pdf(file_path: str):
    """
    Loads a PDF, chunks it, and stores the embeddings in ChromaDB.
    """
    print(f"Processing {file_path}...")
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(docs)

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    
    print(f"Successfully stored {len(chunks)} chunks in ChromaDB.")
    return len(chunks)

def retrieve_context(query: str, k: int = 3) -> str:
    """
    Retrieves the top k most relevant context chunks for a given query.
    """
    try:
        vector_store = get_vector_store()
        # Adding a simple check: if the store is empty, it might throw an error or return nothing.
        results = vector_store.similarity_search(query, k=k)
        if not results:
            return ""
        
        context = "\n\n".join([doc.page_content for doc in results])
        return context
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return ""
