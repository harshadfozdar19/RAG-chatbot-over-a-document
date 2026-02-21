# embeddings.py
import os
# import google.generativeai as genai
from google import genai

# Initialize Gemini API once
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def get_embeddings(texts):
    """
    Generates embeddings using the new Gemini embedding API.
    Works for both single-string and list-of-strings.
    """

    model = "models/embedding-001"

    # Single text → wrap into list
    if isinstance(texts, str):
        texts = [texts]

    embeddings = []
    for t in texts:
        response = genai.embed_content(
            model=model,
            content=t
        )
        embeddings.append(response["embedding"])

    return embeddings
