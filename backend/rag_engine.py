from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHROMA_PERSIST_DIR = "./chroma_db"

embeddings = None

def get_vector_store():
    global embeddings
    if embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    from langchain_chroma import Chroma

    return Chroma(
        collection_name="edu_companion_docs",
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )

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
