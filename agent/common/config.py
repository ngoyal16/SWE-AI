import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Workspace & Environment
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")

    # API Configuration (for agent-server communication)
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Daytona configuration
    DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY", "")
    DAYTONA_TARGET_IMAGE = os.getenv("DAYTONA_TARGET_IMAGE", "daytonaio/langchain-open-swe:0.1.0")
    DAYTONA_SNAPSHOT_NAME = os.getenv("DAYTONA_SNAPSHOT_NAME", "")
    DAYTONA_TARGET_REPO = os.getenv("DAYTONA_TARGET_REPO", "")

    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file") # file or redis

settings = Config()
