import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_KEY_OPENAI = os.getenv("OPENAI_API_KEY")
    API_KEY_GOOGLE = os.getenv("GOOGLE_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "ops-4.5")
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")

    GIT_USERNAME = os.getenv("GIT_USERNAME", "swe-agent")
    GIT_EMAIL = os.getenv("GIT_EMAIL", "swe-agent@example.com")
    GIT_TOKEN = os.getenv("GIT_TOKEN", "")

settings = Config()
