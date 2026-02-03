from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from .config import settings

def get_llm():
    provider = settings.LLM_PROVIDER

    # Backward compatibility logic for specific model names if provider is default/generic
    model_name_legacy = settings.MODEL_NAME.lower()
    if provider == "openai" and "gemini" in model_name_legacy:
        provider = "google"

    if provider == "google":
        if not settings.API_KEY_GOOGLE:
            raise ValueError("GOOGLE_API_KEY is not set for Google provider.")
        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL if settings.LLM_MODEL != "gpt-4-turbo-preview" else "gemini-1.5-pro",
            google_api_key=settings.API_KEY_GOOGLE,
            temperature=0
        )
    elif provider == "azure":
        if not settings.API_KEY_AZURE:
            raise ValueError("AZURE_OPENAI_API_KEY is not set for Azure provider.")
        return AzureChatOpenAI(
            deployment_name=settings.LLM_DEPLOYMENT,
            openai_api_version="2023-05-15", # Example, arguably should be config
            azure_endpoint=settings.LLM_BASE_URL,
            api_key=settings.API_KEY_AZURE,
            temperature=0
        )
    elif provider == "ollama":
        base_url = settings.LLM_BASE_URL or "http://localhost:11434"
        return ChatOllama(
            model=settings.LLM_MODEL,
            base_url=base_url,
            temperature=0
        )
    elif provider == "openai":
        # Supports generic OpenAI compatible endpoints too if BASE_URL is set
        api_key = settings.API_KEY_OPENAI
        if not api_key and not settings.LLM_BASE_URL:
             # Allow missing key only for tests or if using an open proxy?
             # Standard OpenAI requires key.
             pass

        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=api_key,
            base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
