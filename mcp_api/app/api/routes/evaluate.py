from fastapi import APIRouter
from app.models.base import EvaluateRequest, EvaluateResponse
from filesystem_example import mcp_file_server
import pickle
import os
import uuid


router = APIRouter()

# Helper to get pickle file path based on session id
def get_pickle_path(session_id):
    return f"conversation_{session_id}.pkl"

def load_conversation(file_path="conversation.pkl"):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return pickle.load(f)
    return []

def save_conversation(conversation, file_path="conversation.pkl"):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    
    # Save the pickle file
    with open(file_path, "wb") as f:
        pickle.dump(conversation, f)

def conversation_to_string(conversation):
    convo_str = ""
    for msg in conversation:
        convo_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
    return convo_str


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_schema(request: EvaluateRequest):
    user_input = request.input_data
    session_id = request.session_id or str(uuid.uuid4())  # New session if not provided
    print("SessionID obtained: ", session_id)
    file_path = get_pickle_path(session_id)

    if user_input.lower() == "exit":
        if os.path.exists(file_path):
            os.remove(file_path)
        return EvaluateResponse(output=f"Goodbye! Conversation {session_id} ended.", session_id=session_id)

    
    conversation = load_conversation(file_path)
    print(f"Loaded conversation: ", conversation)

    # Add latest user message
    conversation.append({"role": "user", "content": user_input})

    # Run agent on the full conversation
    result = await mcp_file_server.evaluate_schema_question(conversation_to_string(conversation))
    print("result->", result)
    (conversation_to_string(conversation))

    # Add agent's reply to conversation
    conversation.append({"role": "agent", "content": result.final_output})
    save_conversation(conversation, file_path)
    print("conversation saved as", conversation, "on file path: ", file_path)
    
    return EvaluateResponse(output=result.final_output, session_id=session_id)


