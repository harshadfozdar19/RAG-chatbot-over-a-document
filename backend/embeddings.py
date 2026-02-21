# embeddings.py
import os
from google import genai

# Create Gemini client (NEW SDK way)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_embeddings(texts):
    """
    Generates embeddings using Gemini embedding model.
    Works for both single string and list of strings.
    """

    model = "models/embedding-001"

    # Convert single string to list
    if isinstance(texts, str):
        texts = [texts]

    response = client.models.embed_content(
        model=model,
        contents=texts
    )

    # Extract embedding vectors
    return [embedding.values for embedding in response.embeddings]
