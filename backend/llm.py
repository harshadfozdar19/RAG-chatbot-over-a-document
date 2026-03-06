# llm.py
import os

from google import genai
from openai import OpenAI


DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-oss-20b:free"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "gemini").strip().lower()


def _build_history_text(history) -> str:
    history_lines = []
    for msg in history:
        role = msg.get("role", "user").upper()
        text = msg.get("text", "")
        history_lines.append(f"{role}: {text}")
    return "\n".join(history_lines)


def _build_prompt(history, context, question) -> str:
    history_text = _build_history_text(history)
    return f"""
You are an AI assistant inside a RAG system.

Rules:
1. Answer ONLY using the retrieved context.
2. NEVER hallucinate.
3. If answer not found, say EXACTLY:
   "The document does not contain this information."

--- CHAT HISTORY ---
{history_text}

--- RETRIEVED CONTEXT ---
{context}

--- QUESTION ---
{question}
"""


def _answer_with_gemini(prompt: str) -> str:
    client = genai.Client(api_key=_require_env("GEMINI_API_KEY"))
    model_name = os.getenv("LLM_MODEL", DEFAULT_GEMINI_MODEL)
    response = client.models.generate_content(model=model_name, contents=prompt)
    if not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty response.")
    return response.text


def _build_openai_messages(history, context, question):
    system_message = (
        "You are an AI assistant inside a RAG system. "
        "Answer only from the provided context. "
        "If the answer is not in the context, reply exactly with: "
        '"The document does not contain this information."'
    )
    user_prompt = (
        f"CHAT HISTORY:\n{_build_history_text(history)}\n\n"
        f"RETRIEVED CONTEXT:\n{context}\n\n"
        f"QUESTION:\n{question}"
    )
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt},
    ]


def _get_openai_client():
    provider = _get_llm_provider()

    if provider == "openrouter":
        api_key = _require_env("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        headers = {}
        site_url = os.getenv("OPENROUTER_SITE_URL")
        app_name = os.getenv("OPENROUTER_APP_NAME")
        if site_url:
            headers["HTTP-Referer"] = site_url
        if app_name:
            headers["X-Title"] = app_name
        return OpenAI(api_key=api_key, base_url=base_url, default_headers=headers or None)

    if provider in {"openai", "openai-compatible"}:
        api_key = _require_env("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        return OpenAI(api_key=api_key, base_url=base_url)

    raise RuntimeError(
        "Unsupported LLM_PROVIDER. Use one of: gemini, openrouter, openai, openai-compatible"
    )


def _get_openai_model_name() -> str:
    provider = _get_llm_provider()
    if provider == "openrouter":
        return os.getenv("LLM_MODEL", DEFAULT_OPENROUTER_MODEL)
    return os.getenv("LLM_MODEL", DEFAULT_OPENAI_MODEL)


def _extract_openai_text(response) -> str:
    if not getattr(response, "choices", None):
        raise RuntimeError("The model provider returned no choices.")

    message = response.choices[0].message
    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for item in content:
            text_value = getattr(item, "text", None)
            if text_value:
                text_parts.append(text_value)
            elif isinstance(item, dict) and item.get("text"):
                text_parts.append(item["text"])
        final_text = "\n".join(text_parts).strip()
        if final_text:
            return final_text

    raise RuntimeError("The model provider returned an empty response.")


def _answer_with_openai_compatible(history, context, question) -> str:
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=_get_openai_model_name(),
        messages=_build_openai_messages(history, context, question),
        temperature=0.1,
    )
    return _extract_openai_text(response)


def answer_with_context(history, context, question):
    prompt = _build_prompt(history, context, question)
    provider = _get_llm_provider()

    if provider == "gemini":
        return _answer_with_gemini(prompt)

    return _answer_with_openai_compatible(history, context, question)