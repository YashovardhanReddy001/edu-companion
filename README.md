# EduCompanion 🎓

EduCompanion is a single-agent, local intelligent tutoring system designed to help students learn, test their knowledge, and deeply understand their course materials. Built for the IBM SkillsBuild internship, it uses a deterministic AI workflow to provide tailored RAG-based chatting, automated quiz generation, and personalized feedback.

---

## ✨ Features

- **Document Processing**: Upload any PDF course material, which is embedded locally using HuggingFace models and stored in ChromaDB.
- **Intelligent Routing**: The AI determines if you want to chat normally or if you are requesting a quiz.
- **Automated Quizzes**: Generates multiple-choice questions dynamically based on the uploaded context.
- **Tailored Feedback Loop**:
  - 🟢 **Reward**: Answer correctly (>= 70%) and get a gamified, enthusiastic congratulatory response.
  - 🟠 **Relearn**: Answer incorrectly (< 70%) and the AI will break down the concept step-by-step to reteach it simply.
- **Premium UI**: Clean, modern React interface built with TailwindCSS, featuring distinct aesthetic states for different types of AI feedback.

---

## 🏗️ Architecture

EduCompanion relies on a strict LangGraph state machine rather than a generic autonomous agent. This ensures a highly deterministic and educational flow.

```mermaid
graph TD
    %% Nodes
    User([User Message])
    Router[Router Node<br>Intent Analysis]
    RAG[RAG Chat Node<br>Standard QA]
    QuizGen[Quiz Generator Node]
    Eval[Evaluator Node<br>Score 0-100]
    Reward[Reward Node<br>Gamified Congratulation]
    Relearn[Relearn Node<br>Step-by-step Reteach]
    
    %% Edges
    User --> |Is Quiz Active? No| Router
    User --> |Is Quiz Active? Yes| Eval

    Router -- "intent == chat" --> RAG
    Router -- "intent == quiz" --> QuizGen
    
    Eval -- "score >= 70" --> Reward
    Eval -- "score < 70" --> Relearn
    
    classDef node fill:#f8fafc,stroke:#cbd5e1,stroke-width:2px,color:#334155;
    classDef start fill:#e2e8f0,stroke:#94a3b8,stroke-width:2px,color:#0f172a;
    classDef reward fill:#d1fae5,stroke:#34d399,stroke-width:2px,color:#065f46;
    classDef relearn fill:#fef3c7,stroke:#fbbf24,stroke-width:2px,color:#92400e;
    classDef quiz fill:#e0e7ff,stroke:#818cf8,stroke-width:2px,color:#3730a3;
    
    class User start;
    class Router,RAG,Eval node;
    class Reward reward;
    class Relearn relearn;
    class QuizGen quiz;
```

---

## 🛠️ Tech Stack

**Backend**
- Python 3.11+
- FastAPI & Uvicorn
- LangGraph & LangChain (Groq LLM)
- ChromaDB (Local Vector Store)
- HuggingFace Embeddings (`all-MiniLM-L6-v2`)

**Frontend**
- React 18 (TypeScript)
- Vite
- TailwindCSS v4
- Lucide React (Icons)

---

## 🚀 Getting Started (Local Development)

### 1. Clone & Setup Backend
```bash
cd edu-companion/backend
python -m venv venv
# Activate the virtual environment
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```
*Note: Create a `.env` file in the `backend` folder and add your Groq API key: `GROQ_API_KEY=your_key_here`*

### 2. Start the Backend
```bash
uvicorn main:app --reload
```
*Runs on http://localhost:8000*

### 3. Setup & Start Frontend
In a new terminal window:
```bash
cd edu-companion/frontend
npm install
npm run dev
```
*Runs on http://localhost:5173*

---

## 📸 Screenshots

![alt text](image.png)
### Chat Mode
![alt text](image-1.png)
### Reward for a quiz
![alt text](image-2.png)
### Reteach if wrong
