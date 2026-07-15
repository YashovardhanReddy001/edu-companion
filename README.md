# EduCompanion

EduCompanion is a RAG-based learning assistant that lets you upload study PDFs, ask questions, and generate quiz-style interactions from your course material.

## Features

- PDF upload and document chunking
- Retrieval-augmented chat over uploaded material
- Ordinary chat fallback when no study content is available
- Quiz generation and answer evaluation
- FastAPI backend with Groq-powered LLM responses
- Vite + React frontend

## Project Structure

- `backend/` - FastAPI app, graph logic, and retrieval pipeline
- `frontend/` - React UI built with Vite

## Requirements

- Python 3.13+ with the project virtual environment
- Node.js 18+
- A valid `GROQ_API_KEY` in the backend environment

## Setup

### Backend

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with your Groq key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Frontend

```powershell
cd frontend
npm install
```

## Run Locally

### Start Backend

From the repository root:

```powershell
cd backend
..\.venv\Scripts\python.exe main.py
```

The backend runs on:

- `http://localhost:8000`

### Start Frontend

From the repository root:

```powershell
npm --prefix frontend run dev
```

The frontend runs on:

- `http://localhost:5173`
- If that port is busy, Vite may switch to the next available port such as `http://localhost:5174`

## API Endpoints

- `POST /upload` - upload a PDF file
- `POST /chat` - send a chat message

## How It Works

1. You upload a PDF.
2. The backend chunks and stores the content in ChromaDB.
3. Chat requests try to retrieve relevant chunks.
4. If no relevant document content exists, the app falls back to ordinary chat through Groq.
5. If content exists, the LLM answers using the retrieved context.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
