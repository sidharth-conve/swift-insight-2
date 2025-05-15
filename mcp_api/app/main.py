from fastapi import FastAPI
from app.api.routes import evaluate
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL if you want to lock it down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(evaluate.router, prefix="/api")


@app.on_event("shutdown")
def cleanup_conversation_file():
    file_path = "conversation.pkl"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("✅ conversation.pkl deleted on shutdown.")
    else:
        print("⚠️ No conversation.pkl found to delete.")
