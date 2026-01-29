import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Legacy Support (to be deprecated or mapped)
    # MODEL_NAME is still used if specific provider config isn't set
    MODEL_NAME = os.getenv("MODEL_NAME", "ops-4.5")

    # New Dynamic LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower() # openai, google, azure, ollama
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview") # The specific model name
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "") # For local LLMs or Azure
    LLM_DEPLOYMENT = os.getenv("LLM_DEPLOYMENT", "") # For Azure
    LLM_API_KEY = os.getenv("LLM_API_KEY", "") # Generic key (or use specific env vars below)

    # Specific API Keys (backward compat + standard env vars)
    API_KEY_OPENAI = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    API_KEY_GOOGLE = os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
    API_KEY_AZURE = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "./workspace")

    GIT_USERNAME = os.getenv("GIT_USERNAME", "swe-agent")
    GIT_EMAIL = os.getenv("GIT_EMAIL", "swe-agent@example.com")
    GIT_TOKEN = os.getenv("GIT_TOKEN", "")

    # Sandbox configuration
    SANDBOX_TYPE = os.getenv("SANDBOX_TYPE", "local") # local or k8s
    K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
    WORKER_IMAGE = os.getenv("WORKER_IMAGE", "swe-agent-worker:latest") # Image for the worker pod

settings = Config()
