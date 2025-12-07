# pinecone_client.py
import os
from pinecone import Pinecone, ServerlessSpec

_pc = None


def get_pinecone_client():
    """Initialize global Pinecone client once."""
    global _pc
    if _pc is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY missing in .env")

        _pc = Pinecone(api_key=api_key)
    return _pc


def get_or_create_index():
    """Create index if missing, return index object."""
    pc = get_pinecone_client()

    index_name = os.getenv("PINECONE_INDEX", "rag-index")
    cloud = os.getenv("PINECONE_CLOUD", "aws")
    region = os.getenv("PINECONE_REGION", "us-east-1")

    # Create fresh index if missing
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,            # MUST match embedding model
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )

    return pc.Index(index_name)


def clear_index_on_startup():
    """
    Called ONLY ONCE when FastAPI server boots.
    Clears *all* vectors but keeps index metadata.
    """
    index = get_or_create_index()

    try:
        print("\n🗑️ Clearing ALL vectors from Pinecone (startup wipe)...")
        index.delete(delete_all=True)
        print("✔ Pinecone index is now EMPTY.\n")
    except Exception as e:
        print("⚠️ Warning: Could not clear index:", e)
