from __future__ import annotations

import os

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
COLLECTION_NAME = "visa_rules"
EMBEDDING_MODEL = "default"  # all-MiniLM-L6-v2 via ONNXRuntime — no PyTorch required
_N_RESULTS = 5


def _get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )


def search(scenario: str, n_results: int = _N_RESULTS) -> list[dict]:
    """Return the top-n VISA rule chunks most relevant to *scenario*.

    Each result dict contains:
        condition_id  str  — e.g. "13.1"
        title         str  — section heading
        snippet       str  — raw text chunk
        score         float — cosine similarity (higher = more relevant)
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[scenario],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    candidates: list[dict] = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(docs, metas, distances):
        candidates.append(
            {
                "condition_id": meta.get("condition_id", ""),
                "title": meta.get("title", ""),
                "snippet": doc,
                "score": round(1.0 - dist, 4),  # cosine distance → similarity
            }
        )

    return candidates


def upsert_chunks(chunks: list[tuple[str, str, str, str]]) -> None:
    """Insert or update chunks in the collection.

    Args:
        chunks: list of (chunk_id, condition_id, title, text)
    """
    collection = _get_collection()
    ids = [c[0] for c in chunks]
    documents = [c[3] for c in chunks]
    metadatas = [{"condition_id": c[1], "title": c[2]} for c in chunks]
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def reset_collection() -> None:
    """Drop and recreate the collection (use before a full re-ingest)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
    client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )
