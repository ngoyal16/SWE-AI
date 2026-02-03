from typing import Optional
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from .config import settings
from ..agent import AgentManager

def get_llm(session_id: Optional[str] = None):
    # Default Config
    provider = settings.LLM_PROVIDER
    model_name = settings.LLM_MODEL
    base_url = settings.LLM_BASE_URL
    deployment = settings.LLM_DEPLOYMENT

    # Use generic key for all defaults
    api_key_default = settings.LLM_API_KEY
    api_key_google = api_key_default
    api_key_azure = api_key_default
    api_key_openai = api_key_default

    # Session Override
    if session_id:
        manager = AgentManager()
        ai_config = manager.get_ai_config(session_id)
        if ai_config:
            provider = ai_config.provider
            model_name = ai_config.model

            if provider == "google":
                api_key_google = ai_config.api_key
            elif provider == "azure":
                api_key_azure = ai_config.api_key
                base_url = ai_config.base_url
                deployment = ai_config.model # Use model name as deployment name for Azure
            elif provider == "openai":
                api_key_openai = ai_config.api_key
                base_url = ai_config.base_url
            # ollama might not need keys, just base_url
            elif provider == "ollama":
                if ai_config.base_url:
                    base_url = ai_config.base_url

    if provider == "google":
        if not api_key_google:
             # If using session config, ensure key is present
             if session_id:
                 raise ValueError(f"Google API Key is missing for session {session_id}.")
             raise ValueError("LLM_API_KEY is not set for Google provider.")

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key_google,
            temperature=0
        )
    elif provider == "azure":
        if not api_key_azure:
            if session_id:
                 raise ValueError(f"Azure API Key is missing for session {session_id}.")
            raise ValueError("LLM_API_KEY is not set for Azure provider.")
        return AzureChatOpenAI(
            deployment_name=deployment,
            openai_api_version="2023-05-15",
            azure_endpoint=base_url,
            api_key=api_key_azure,
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
        # Supports generic OpenAI compatible endpoints too if BASE_URL is set
        if not api_key_openai and not base_url:
             # Allow missing key only if strictly necessary or local?
             pass

        return ChatOpenAI(
            model=model_name,
            api_key=api_key_openai,
            base_url=base_url if base_url else None,
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
