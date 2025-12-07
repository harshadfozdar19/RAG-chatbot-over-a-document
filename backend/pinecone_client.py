# pinecone_client.py
import os
from pinecone import ServerlessSpec

_pc = None
_index = None


def get_pinecone_client():
    """
    Lazy-load Pinecone client so it doesn't
    occupy memory during server startup.
    """
    global _pc
    if _pc is None:
        from pinecone import Pinecone   # lazy import
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY missing!")
        _pc = Pinecone(api_key=api_key)

    return _pc


def get_or_create_index():
    """
    Lazily create + return index.
    No auto delete to avoid Render memory spike.
    """
    global _index

    if _index is not None:
        return _index

    pc = get_pinecone_client()

    index_name = os.getenv("PINECONE_INDEX", "rag-index")
    cloud = os.getenv("PINECONE_CLOUD", "aws")
    region = os.getenv("PINECONE_REGION", "us-east-1")

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )

    _index = pc.Index(index_name)
    return _index
