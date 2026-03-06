# embeddings.py
import os

from google import genai
from openai import OpenAI


DEFAULT_GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_embedding_provider() -> str:
    return os.getenv("EMBEDDING_PROVIDER", "gemini").strip().lower()


def get_embedding_dimension() -> int:
    provider = get_embedding_provider()
    if provider == "openai":
        return int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    return int(os.getenv("EMBEDDING_DIMENSION", "768"))


def _get_gemini_embeddings(texts):
    client = genai.Client(api_key=_require_env("GEMINI_API_KEY"))
    model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_GEMINI_EMBEDDING_MODEL)
    response = client.models.embed_content(
        model=model_name,
        contents=texts,
        config={"output_dimensionality": get_embedding_dimension()},
    )
    return [embedding.values for embedding in response.embeddings]


def _get_openai_embeddings(texts):
    client = OpenAI(
        api_key=_require_env("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)
    response = client.embeddings.create(model=model_name, input=texts)
    return [item.embedding for item in response.data]


def get_embeddings(texts):
    """
    Generate embeddings using the configured embedding provider.
    """

    if isinstance(texts, str):
        texts = [texts]

    provider = get_embedding_provider()
    if provider == "gemini":
        return _get_gemini_embeddings(texts)
    if provider == "openai":
        return _get_openai_embeddings(texts)

    raise RuntimeError("Unsupported EMBEDDING_PROVIDER. Use one of: gemini, openai")