import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Workspace & Environment
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")

    # API Configuration (for agent-server communication)
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

    # LLM Defaults (System-wide fallbacks)
    # These are only used if a session does not have specific AI credentials
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
    LLM_DEPLOYMENT = os.getenv("LLM_DEPLOYMENT", "")

    # Optional: System-wide keys (for testing or fallback)
    # Ideally, these should be removed in production in favor of session-scoped credentials
    API_KEY_OPENAI = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    API_KEY_GOOGLE = os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
    API_KEY_AZURE = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

    # Legacy Support
    MODEL_NAME = os.getenv("MODEL_NAME", "ops-4.5")

    # Daytona configuration
    DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY", "")
    DAYTONA_TARGET_IMAGE = os.getenv("DAYTONA_TARGET_IMAGE", "daytonaio/langchain-open-swe:0.1.0")
    DAYTONA_SNAPSHOT_NAME = os.getenv("DAYTONA_SNAPSHOT_NAME", "")
    DAYTONA_TARGET_REPO = os.getenv("DAYTONA_TARGET_REPO", "")

    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file") # file or redis

settings = Config()
