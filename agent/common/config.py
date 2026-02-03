import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Legacy Support
    MODEL_NAME = os.getenv("MODEL_NAME", "ops-4.5")

    # New Dynamic LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
    LLM_DEPLOYMENT = os.getenv("LLM_DEPLOYMENT", "")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")

    API_KEY_OPENAI = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    API_KEY_GOOGLE = os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
    API_KEY_AZURE = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")

    # API Configuration (for agent-server communication)
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

    # DEPRECATED: Git credentials are now fetched dynamically from the server
    # These are kept temporarily for backward compatibility during migration
    # TODO: Remove these after confirming dynamic credentials work in production


    # Daytona configuration
    DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY", "")
    DAYTONA_TARGET_IMAGE = os.getenv("DAYTONA_TARGET_IMAGE", "daytonaio/langchain-open-swe:0.1.0")
    DAYTONA_SNAPSHOT_NAME = os.getenv("DAYTONA_SNAPSHOT_NAME", "")
    DAYTONA_TARGET_REPO = os.getenv("DAYTONA_TARGET_REPO", "")

    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file") # file or redis

settings = Config()
