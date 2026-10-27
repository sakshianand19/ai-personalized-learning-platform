"""Azure OpenAI chat model wiring.

Every LLM-backed service accepts ``llm: BaseChatModel | None``. ``None`` means Azure
OpenAI is not configured and the service falls back to deterministic heuristics, so
the API stays fully functional (and testable) without credentials.
"""

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.config import get_settings


@lru_cache
def _azure_chat_model(
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
    temperature: float,
    timeout: float,
) -> BaseChatModel:
    from langchain_openai import AzureChatOpenAI

    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        azure_deployment=deployment,
        temperature=temperature,
        timeout=timeout,
        max_retries=2,
    )


def get_llm() -> BaseChatModel | None:
    """FastAPI dependency returning the configured chat model (overridden in tests)."""
    settings = get_settings()
    if not settings.azure_openai_configured:
        return None
    return _azure_chat_model(
        settings.azure_openai_endpoint,
        settings.azure_openai_api_key,
        settings.azure_openai_api_version,
        settings.azure_openai_deployment,
        settings.llm_temperature,
        settings.llm_timeout_seconds,
    )


def llm_provider_name() -> str:
    return "azure_openai" if get_settings().azure_openai_configured else "heuristic"
