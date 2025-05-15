from pydantic import BaseModel
from typing import Any, Optional


class MessageResponse(BaseModel):
    message: Any

class EvaluateRequest(BaseModel):
    input_data: str
    session_id: Optional[str] = None

class EvaluateResponse(BaseModel):
    output: str
    session_id: str  # always return session id
