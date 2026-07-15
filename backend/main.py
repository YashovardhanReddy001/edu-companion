from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil

from rag_engine import process_and_store_pdf
from graph import graph, State
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="EduCompanion API")

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
    
    config = {"configurable": {"thread_id": req.thread_id}}
    
    try:
        # Run graph
        final_state = graph.invoke(initial_state, config=config)
        
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
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
