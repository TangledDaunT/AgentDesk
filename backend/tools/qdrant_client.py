"""Qdrant vector store tools for memory and data agent."""

import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

from config import get_settings

settings = get_settings()

# Initialize Qdrant client
_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client singleton."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            prefer_grpc=False,
        )
    return _qdrant_client


def ensure_collection():
    """Ensure memory collection exists."""
    client = get_qdrant_client()

    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if settings.qdrant_collection not in collection_names:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Created Qdrant collection: {settings.qdrant_collection}")


# Simple embedding function - using sentence-transformers if available, else mock
_embedding_model = None


def _get_embedding(text: str) -> List[float]:
    """Get embedding vector for text."""
    global _embedding_model

    try:
        if _embedding_model is None:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        embedding = _embedding_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        # Fallback: use simple weighted average of token hashes
        # This is NOT for production - only for demo without the model
        print(f"Warning: Using fallback embedding (install sentence-transformers for better results)")
        tokens = text.lower().split()[:50]
        vec = np.zeros(384, dtype=np.float32)
        for i, token in enumerate(tokens):
            np.random.seed(hash(token) % (2**32))
            noise = np.random.randn(384).astype(np.float32)
            vec += noise * (1.0 / (i + 1))

        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()


async def add_to_memory(
    content: str,
    summary: str,
    kind: str = "outcome",
    metadata: Optional[Dict] = None,
) -> str:
    """
    Add a memory record to Qdrant.

    Args:
        content: Full content to embed
        summary: Short summary for display
        kind: Type of memory (outcome, lesson, etc.)
        metadata: Additional metadata

    Returns:
        ID of the created memory record
    """
    ensure_collection()
    client = get_qdrant_client()

    memory_id = str(uuid.uuid4())
    embedding = _get_embedding(content)

    point = PointStruct(
        id=memory_id,
        vector=embedding,
        payload={
            "id": memory_id,
            "summary": summary,
            "kind": kind,
            "content": content,
            "metadata": metadata or {},
        },
    )

    client.upsert(
        collection_name=settings.qdrant_collection,
        points=[point],
    )

    return memory_id


async def query_memory(
    query: str,
    limit: int = 5,
    min_score: float = 0.5,
) -> List[Dict]:
    """
    Query memory store for relevant documents.

    Args:
        query: Query text
        limit: Maximum results
        min_score: Minimum similarity score

    Returns:
        List of matching memory records with scores
    """
    ensure_collection()
    client = get_qdrant_client()

    embedding = _get_embedding(query)

    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=embedding,
        limit=limit,
        score_threshold=min_score,
    )

    return [
        {
            "id": r.payload.get("id"),
            "summary": r.payload.get("summary"),
            "kind": r.payload.get("kind"),
            "score": r.score,
            "content": r.payload.get("content"),
        }
        for r in results
    ]


async def retrieve_similar_tasks(task_description: str, limit: int = 3) -> List[Dict]:
    """
    Retrieve similar past tasks to use as context.

    Args:
        task_description: Description of current task
        limit: Max results

    Returns:
        List of similar past task outcomes
    """
    return await query_memory(
        query=task_description,
        limit=limit,
        min_score=0.6,
    )
