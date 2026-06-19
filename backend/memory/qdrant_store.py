"""Qdrant-based long-term memory store."""

import uuid
from datetime import datetime
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import get_settings

settings = get_settings()


class QdrantMemoryStore:
    """Long-term memory storage using Qdrant vector database."""

    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url, prefer_grpc=False)
        self.collection_name = settings.qdrant_collection
        self._ensure_collection()

        # Lazy-load embedding model
        self._embedding_model = None

    def _ensure_collection(self):
        """Ensure the memory collection exists."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            print(f"Created Qdrant collection: {self.collection_name}")

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )

        import numpy as np
        embedding = self._embedding_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def write(
        self,
        content: str,
        summary: str,
        kind: str = "outcome",
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        """
        Write a memory record.

        Args:
            content: Full content to embed and store
            summary: Short summary for display
            kind: Type of memory (outcome, lesson)
            task_id: Associated task ID
            agent_id: Agent that created this memory

        Returns:
            Memory record ID
        """
        memory_id = str(uuid.uuid4())
        embedding = self._get_embedding(content)

        point = PointStruct(
            id=memory_id,
            vector=embedding,
            payload={
                "id": memory_id,
                "summary": summary,
                "kind": kind,
                "content": content,
                "task_id": task_id,
                "agent_id": agent_id,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

        return memory_id

    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.5,
    ) -> List[Dict]:
        """
        Search memory by semantic similarity.

        Args:
            query: Query text
            limit: Max results
            min_score: Minimum similarity threshold

        Returns:
            List of matching memory records
        """
        embedding = self._get_embedding(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=limit,
            score_threshold=min_score,
        )

        return [
            {
                "id": r.payload.get("id"),
                "summary": r.payload.get("summary"),
                "kind": r.payload.get("kind"),
                "content": r.payload.get("content"),
                "task_id": r.payload.get("task_id"),
                "agent_id": r.payload.get("agent_id"),
                "created_at": r.payload.get("created_at"),
                "score": r.score,
            }
            for r in results
        ]

    async def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent memory records."""
        # Qdrant doesn't support sort by payload, so we use a scroll
        results = self.client.scroll(
            collection_name=self.collection_name,
            limit=limit * 2,  # Get more to sort
            with_payload=True,
        )[0]

        # Sort by created_at desc
        sorted_results = sorted(
            results,
            key=lambda r: r.payload.get("created_at", ""),
            reverse=True,
        )[:limit]

        return [
            {
                "id": r.payload.get("id"),
                "summary": r.payload.get("summary"),
                "kind": r.payload.get("kind"),
                "createdAt": r.payload.get("created_at"),
            }
            for r in sorted_results
        ]

    def seed_sample_data(self):
        """Seed Qdrant with sample documents for demo."""
        samples = [
            {
                "content": "Qdrant vector database with Qwen embeddings achieved 94% accuracy on legal document similarity matching. The combination performed especially well on contract clause identification.",
                "summary": "Qdrant + Qwen embeddings hit 94% match accuracy on legal corpus",
                "kind": "outcome",
            },
            {
                "content": "Redis caching layer reduced RAG query latency from 1.1 seconds to 400ms average. Cache hit rate was 78% for repeated queries.",
                "summary": "Redis caching cut RAG query latency from 1.1s to 400ms",
                "kind": "outcome",
            },
            {
                "content": "Web search agent consistently times out when querying rate-limited sources. The 8 second timeout threshold is too short for academic paper databases.",
                "summary": "Web search agent times out above 8s on rate-limited sources",
                "kind": "lesson",
            },
            {
                "content": "Code agent performed well on Python refactoring tasks but struggled with JavaScript async patterns. Tool call accuracy was 91% overall.",
                "summary": "Code agent achieved 91% tool-call accuracy on Python tasks",
                "kind": "outcome",
            },
            {
                "content": "Planner agent's task decomposition works best when goals are under 200 tokens. Longer goals result in over-decomposition (too many subtasks).",
                "summary": "Planner works best with goals under 200 tokens",
                "kind": "lesson",
            },
        ]

        import numpy as np

        points = []
        for sample in samples:
            memory_id = str(uuid.uuid4())
            embedding = self._get_embedding(sample["content"])

            point = PointStruct(
                id=memory_id,
                vector=embedding,
                payload={
                    "id": memory_id,
                    "summary": sample["summary"],
                    "kind": sample["kind"],
                    "content": sample["content"],
                    "created_at": datetime.utcnow().isoformat(),
                    "seeded": True,
                },
            )
            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        print(f"Seeded {len(points)} sample memory records")
