import os
import json
from typing import TypedDict, Annotated, List, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from backend.rag_engine import retrieve_context

load_dotenv()

# Ensure GROQ_API_KEY is available
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(temperature=0.7, model_name="llama-3.3-70b-versatile", groq_api_key=groq_api_key)
llm_json = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", groq_api_key=groq_api_key).bind(response_format={"type": "json_object"})

# Define State
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    context: str
    quiz_active: bool
    last_score: int
    metadata: dict  # To pass UI instructions like 'reward' or 'relearn'

# Nodes

def router_node(state: State):
    """
    Analyzes the latest user message to route the conversation.
    Decides if the user wants to chat normally, take a quiz, or if they are answering an active quiz.
    """
    if state.get("quiz_active"):
        return {"messages": []} # Proceed to evaluator_node (no direct routing from here yet, handled by conditional edges)
    
    last_message = state["messages"][-1].content
    
    prompt = f"""
    Analyze the following user input and determine their intent.
    Is the user asking for a quiz/test/assessment, or are they asking a general question?
    Respond in JSON format: {{"intent": "quiz" | "chat"}}
    User Input: {last_message}
    """
    
    response = llm_json.invoke([HumanMessage(content=prompt)])
    try:
        result = json.loads(response.content)
        intent = result.get("intent", "chat")
    except:
        intent = "chat"
        
    # We don't update state here except metadata for routing if needed, but standard routing uses the return value in conditional edges.
    # To use in conditional edge, we can add it to metadata or just let the edge function do the check.
    # Actually, returning a dict updates the state. Let's store intent in metadata.
    metadata = state.get("metadata", {})
    metadata["intent"] = intent
    return {"metadata": metadata}


def rag_chat_node(state: State):
    """Handles standard QA with RAG."""
    last_message = state["messages"][-1].content
    context = retrieve_context(last_message)

    if context:
        sys_prompt = f"""You are EduCompanion, a helpful and encouraging intelligent tutoring system.
Use the following retrieved context to answer the student's questions.
If you don't know the answer based on the context, you can use your general knowledge but mention that it's not from the uploaded materials.

Context:
{context}
"""
        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            *state["messages"]
        ])
    else:
        sys_prompt = """You are EduCompanion, a helpful and encouraging intelligent tutoring system.
No uploaded study context is available right now, so answer naturally as an ordinary chat assistant.
Be concise, clear, and helpful.
"""
        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            *state["messages"]
        ])
    
    return {"messages": [response], "context": context, "metadata": {"type": "chat"}}

def quiz_generator_node(state: State):
    """Generates a 1-question multiple choice quiz based on context."""
    # Retrieve general context if none exists for the specific query, or use previous context
    context = state.get("context", "")
    if not context:
        context = retrieve_context("Generate a general question about the main topic.")
        
    prompt = f"""You are an expert tutor. Based on the following context, generate a single multiple-choice question to test the student's understanding.
    Format the output clearly with the question and 4 options (A, B, C, D).
    Do NOT provide the answer in your response, just the question and options.
    
    Context:
    {context}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {
        "messages": [response],
        "quiz_active": True,
        "context": context,
        "metadata": {"type": "quiz_question"}
    }

def evaluator_node(state: State):
    """Evaluates the user's answer to the quiz."""
    user_answer = state["messages"][-1].content
    quiz_question = state["messages"][-2].content if len(state["messages"]) > 1 else ""
    context = state.get("context", "")
    
    prompt = f"""You are an expert evaluator. 
    The student was asked the following question:
    {quiz_question}
    
    Based on this context: {context}
    
    The student answered: {user_answer}
    
    Evaluate if the student's answer is correct. 
    Provide a score between 0 and 100. 100 for correct, 0 for incorrect.
    Respond in JSON format ONLY: {{"score": integer}}
    """
    
    response = llm_json.invoke([HumanMessage(content=prompt)])
    try:
        result = json.loads(response.content)
        score = int(result.get("score", 0))
    except:
        score = 0
        
    return {"last_score": score, "quiz_active": False}

def reward_node(state: State):
    """Generates a gamified, enthusiastic congratulatory message."""
    prompt = "The student just answered a quiz question correctly! Generate an extremely enthusiastic, gamified congratulatory message. Keep it brief but highly encouraging."
    response = llm.invoke([SystemMessage(content=prompt)])
    
    return {"messages": [response], "metadata": {"type": "reward"}}

def relearn_node(state: State):
    """Breaks down the concept step-by-step and reteaches it simply."""
    quiz_question = state["messages"][-3].content if len(state["messages"]) > 2 else ""
    context = state.get("context", "")
    
    sys_prompt = f"""The student answered a question incorrectly. 
    Question: {quiz_question}
    
    Context: {context}
    
    Break down the correct concept step-by-step and reteach it in a very simple, supportive, and easy-to-understand way. Do not be condescending. Use analogies if helpful.
    """
    
    response = llm.invoke([SystemMessage(content=sys_prompt)])
    
    return {"messages": [response], "metadata": {"type": "relearn"}}


# Conditional Routing Functions
def route_initial(state: State) -> Literal["rag_chat_node", "quiz_generator_node", "evaluator_node"]:
    if state.get("quiz_active"):
        return "evaluator_node"
    
    intent = state.get("metadata", {}).get("intent", "chat")
    if intent == "quiz":
        return "quiz_generator_node"
    return "rag_chat_node"

def route_evaluation(state: State) -> Literal["reward_node", "relearn_node"]:
    score = state.get("last_score", 0)
    if score >= 70:
        return "reward_node"
    return "relearn_node"

# Build Graph
builder = StateGraph(State)

builder.add_node("router_node", router_node)
builder.add_node("rag_chat_node", rag_chat_node)
builder.add_node("quiz_generator_node", quiz_generator_node)
builder.add_node("evaluator_node", evaluator_node)
builder.add_node("reward_node", reward_node)
builder.add_node("relearn_node", relearn_node)

builder.set_entry_point("router_node")

builder.add_conditional_edges(
    "router_node",
    route_initial
)

builder.add_edge("rag_chat_node", END)
builder.add_edge("quiz_generator_node", END)

builder.add_conditional_edges(
    "evaluator_node",
    route_evaluation
)

builder.add_edge("reward_node", END)
builder.add_edge("relearn_node", END)

# Compile
graph = builder.compile()
