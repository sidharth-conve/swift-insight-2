from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    PROJECT_NAME: str = "FastAPI Boilerplate"
    API_VERSION: str = "v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()
