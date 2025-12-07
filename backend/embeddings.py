# embeddings.py
from sentence_transformers import SentenceTransformer

# FREE embedding model — 384 dimensions
embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text: str):
    return embed_model.encode(text).tolist()

def get_embeddings(texts):
    return embed_model.encode(texts).tolist()
