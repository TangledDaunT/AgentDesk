#!/usr/bin/env python3
"""Seed Qdrant with sample documents for demo."""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.qdrant_store import QdrantMemoryStore


def main():
    """Seed Qdrant with sample documents."""
    print("Initializing Qdrant connection...")
    store = QdrantMemoryStore()

    print("Seeding sample documents...")
    store.seed_sample_data()

    print("\nVerifying seeded data...")
    import asyncio

    async def verify():
        results = await store.search("vector database", limit=3)
        print(f"Found {len(results)} results for test query")
        for r in results:
            print(f"  - {r.get('summary', 'Unknown')[:60]}...")

    asyncio.run(verify())
    print("\nSeeding complete!")


if __name__ == "__main__":
    main()
