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

    GIT_USERNAME = os.getenv("GIT_USERNAME", "swe-agent")
    GIT_EMAIL = os.getenv("GIT_EMAIL", "swe-agent@example.com")

    GIT_COMMIT_AUTHOR_NAME = os.getenv("GIT_COMMIT_AUTHOR_NAME", "swe-agent")
    GIT_COMMIT_AUTHOR_EMAIL = os.getenv("GIT_COMMIT_AUTHOR_EMAIL", "swe-agent@example.com")

    GIT_TOKEN = os.getenv("GIT_TOKEN", "")
    # GIT_HOST_TOKENS should be a JSON string mapping hostname -> token
    GIT_HOST_TOKENS = os.getenv("GIT_HOST_TOKENS", "")

    # Sandbox configuration
    SANDBOX_TYPE = os.getenv("SANDBOX_TYPE", "local")
    K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
    WORKER_IMAGE = os.getenv("WORKER_IMAGE", "swe-agent-worker:latest")
    SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "swe-agent-sandbox:latest")
    K8S_RUNTIME_CLASS = os.getenv("K8S_RUNTIME_CLASS", None) # For MicroVM support

    # Daytona configuration
    DAYTONA_API_KEY = os.getenv("DAYTONA_API_KEY", "")
    DAYTONA_SERVER_URL = os.getenv("DAYTONA_SERVER_URL", "https://api.daytona.io")
    DAYTONA_TARGET_IMAGE = os.getenv("DAYTONA_TARGET_IMAGE", "ubuntu:22.04")
    DAYTONA_TARGET_REPO = os.getenv("DAYTONA_TARGET_REPO", "")

    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file") # file or redis

settings = Config()
