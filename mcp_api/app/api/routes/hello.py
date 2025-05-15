from fastapi import APIRouter
from app.models.base import MessageResponse

router = APIRouter()

@router.post("/hello", response_model=MessageResponse)
async def say_hello():
    return {"message": "Hello, world!"}
