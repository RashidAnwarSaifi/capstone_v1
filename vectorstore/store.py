"""Vector-based knowledge store used for semantic similarity search.

Embeddings are generated locally (see vectorstore/embeddings.py - no
external API key needed) and persisted on disk via Chroma, so the
knowledge base survives across app restarts."""

import uuid

import chromadb

from config import settings
from vectorstore.embeddings import get_embedder

_COLLECTION_NAME = "documents"


class VectorStore:
    def __init__(self):
        self._client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        self._collection = self._client.get_or_create_collection(_COLLECTION_NAME)
        self._embedder = None  # lazy: only load the HF model once embedding is actually needed

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder.embed(texts)

    def add_documents(self, chunks: list[str], source: str) -> int:
        if not chunks:
            return 0
        embeddings = self._embed(chunks)
        ids = [f"{source}-{uuid.uuid4().hex[:8]}-{i}" for i in range(len(chunks))]
        metadatas = [{"source": source} for _ in chunks]
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def query(
        self, query_text: str, top_k: int = None, sources: list[str] | None = None
    ) -> list[dict]:
        top_k = top_k or settings.TOP_K
        if self._collection.count() == 0:
            return []
        query_embedding = self._embed([query_text])[0]
        where = {"source": {"$in": sources}} if sources else None
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            where=where,
        )
        hits = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(documents, metadatas, distances):
            hits.append({"text": doc, "source": meta.get("source", "unknown"), "distance": dist})
        return hits

    def list_sources(self) -> list[str]:
        data = self._collection.get()
        sources = {m.get("source", "unknown") for m in data.get("metadatas", [])}
        return sorted(sources)

    def delete_source(self, source: str) -> None:
        self._collection.delete(where={"source": source})

    def clear(self):
        self._client.delete_collection(_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(_COLLECTION_NAME)