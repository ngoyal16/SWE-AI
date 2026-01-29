from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

def get_llm():
    model_name = settings.MODEL_NAME.lower()

    if "gemini-3.5" in model_name:
        if not settings.API_KEY_GOOGLE:
            raise ValueError("GOOGLE_API_KEY is not set for Gemini model.")
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=settings.API_KEY_GOOGLE,
            temperature=0
        )
    elif "ops-4.5" in model_name:
        if not settings.API_KEY_OPENAI:
            # For testing/mocking we might want to allow initialization without key if mocked
            pass
        return ChatOpenAI(
            model="gpt-4-turbo-preview",
            api_key=settings.API_KEY_OPENAI,
            temperature=0
        )
    else:
        # Default fallback or error
        raise ValueError(f"Unsupported model name: {model_name}")
