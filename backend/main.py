from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
import os
import shutil

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

from backend.rag_engine import process_and_store_pdf
from backend.graph import graph, State
from langchain_core.messages import HumanMessage, AIMessage
from backend.rag_engine import get_vector_store

app = FastAPI(title="EduCompanion API")

# Initialize the Langfuse client before creating the callback handler.
langfuse_client = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    base_url=os.getenv("LANGFUSE_HOST"),
)

# Langfuse's Langchain callback handler expects `public_key` (and optional trace_context).
langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY")
)

# Configure CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"], # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    message: str
    thread_id: str
    messages_history: List[dict] # [{role: 'user', content: 'hi'}, ...]
    context: str = ""
    quiz_active: bool = False
    last_score: int = 0

class ChatResponse(BaseModel):
    messages: List[dict]
    context: str
    quiz_active: bool
    last_score: int
    metadata: dict

# The `/chat` route below is the primary chat handler. We integrate Langfuse
# by passing the `langfuse_handler` in the `config.callbacks` when invoking
# the graph asynchronously.

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        chunks_count = process_and_store_pdf(file_path)
        return {"message": f"Successfully processed and stored {chunks_count} chunks from {file.filename}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    # Convert incoming dict history to LangChain messages
    formatted_messages = []
    for msg in req.messages_history:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            continue
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        else:
            formatted_messages.append(AIMessage(content=msg["content"]))
            
    # Add the new message
    formatted_messages.append(HumanMessage(content=req.message))
    
    initial_state = {
        "messages": formatted_messages,
        "context": req.context,
        "quiz_active": req.quiz_active,
        "last_score": req.last_score,
        "metadata": {}
    }
    
    # Include Langfuse callback in the invocation config so traces are sent
    config = {
        "configurable": {"thread_id": req.thread_id},
        "callbacks": [langfuse_handler]
    }

    try:
        # Run graph asynchronously so we can attach Langfuse callbacks
        final_state = await graph.ainvoke(initial_state, config=config)
        
        # Format outgoing messages
        out_messages = []
        for msg in final_state.get("messages", []):
            role = "user" if isinstance(msg, HumanMessage) else "ai"
            out_messages.append({"role": role, "content": msg.content})
            
        return ChatResponse(
            messages=out_messages,
            context=final_state.get("context", ""),
            quiz_active=final_state.get("quiz_active", False),
            last_score=final_state.get("last_score", 0),
            metadata=final_state.get("metadata", {})
        )
    except Exception as e:
        print(f"Graph execution error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the chat.")

if __name__ == "__main__":
    import uvicorn
    # In development we used `--reload` which restarts the process and re-initializes
    # heavy models often. For a stable, faster runtime disable reload.
    uvicorn.run("main:app", host="localhost", port=8000, reload=False)


# Preload heavy models on startup to avoid per-request loading latency
@app.on_event("startup")
async def _preload_models():
    try:
        # Warm the embedding model and vector store once at startup
        get_vector_store()
        print("Preloaded embedding model and vector store.")
    except Exception as e:
        print(f"Warning: failed to preload vector store: {e}")
