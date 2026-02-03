from typing import Optional
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from ..agent import AgentManager

def get_llm(session_id: str):
    """
    Retrieve the LLM instance based on the session's active AI configuration.
    Strictly requires a session_id and a registered AI config.
    """
    if not session_id:
        raise ValueError("session_id is required to retrieve LLM configuration.")

    manager = AgentManager()
    ai_config = manager.get_ai_config(session_id)

    if not ai_config:
        raise ValueError(f"No active AI configuration found for session {session_id}. Worker must fetch credentials first.")

    provider = ai_config.provider
    model_name = ai_config.model
    api_key = ai_config.api_key
    base_url = ai_config.base_url
    deployment = None

    # Provider-specific adjustments
    if provider == "azure":
        deployment = ai_config.model # Use model name as deployment name for Azure

    if provider == "google":
        if not api_key:
             raise ValueError(f"Google API Key is missing for session {session_id}.")

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0
        )
    elif provider == "azure":
        if not api_key:
             raise ValueError(f"Azure API Key is missing for session {session_id}.")
        return AzureChatOpenAI(
            deployment_name=deployment,
            openai_api_version="2023-05-15",
            azure_endpoint=base_url,
            api_key=api_key,
            temperature=0
        )
    elif provider == "ollama":
        final_base_url = base_url or "http://localhost:11434"
        return ChatOllama(
            model=model_name,
            base_url=final_base_url,
            temperature=0
        )
    elif provider == "openai":
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url if base_url else None,
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
