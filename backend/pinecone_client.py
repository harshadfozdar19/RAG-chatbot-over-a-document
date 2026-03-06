# pinecone_client.py
import os
from pinecone import Pinecone, ServerlessSpec

from embeddings import get_embedding_dimension

_pc = None
_index = None


def get_pinecone_client():
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return _pc


def get_or_create_index():
    global _index

    if _index is not None:
        return _index

    pc = get_pinecone_client()

    index_name = os.getenv("PINECONE_INDEX", "rag-index-gemini")
    cloud = os.getenv("PINECONE_CLOUD", "aws")
    region = os.getenv("PINECONE_REGION", "us-east-1")
    embedding_dimension = get_embedding_dimension()

    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=embedding_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
    else:
        index_info = pc.describe_index(name=index_name)
        if index_info.dimension != embedding_dimension:
            raise RuntimeError(
                f"Pinecone index '{index_name}' has dimension {index_info.dimension}, "
                f"but the configured embedding provider requires {embedding_dimension}. "
                "Use a matching EMBEDDING_PROVIDER/EMBEDDING_DIMENSION pair or a different PINECONE_INDEX."
            )

    _index = pc.Index(index_name)
    return _index