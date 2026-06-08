"""Embedding provider abstraction for Milestone 4.

Per PRODUCT_SPEC §17 and §28:
- Provider-agnostic interface.
- embed_texts(list[str]) -> list[list[float]]
- embed_query(str) -> list[float]
- Fake for tests (deterministic, no external calls).
- Real: openai_compatible using AI_EMBEDDING_* env vars.
"""
import os
from typing import List, Optional

import httpx  # will be added to deps

from ..config import (
    AI_EMBEDDING_PROVIDER,
    AI_EMBEDDING_BASE_URL,
    AI_EMBEDDING_API_KEY,
    AI_EMBEDDING_MODEL,
    AI_EMBEDDING_DIMENSIONS,
)


class EmbeddingProvider:
    """Abstract base for embedding providers."""

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        """Default: embed single query as list of one, return first."""
        vecs = self.embed_texts([text])
        return vecs[0] if vecs else []


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic fake provider for tests and offline dev.
    Produces consistent vectors based on text hash. No network.
    """

    def __init__(self, dimensions: Optional[int] = None):
        self.dimensions = dimensions or AI_EMBEDDING_DIMENSIONS

    def _fake_vector(self, text: str) -> List[float]:
        if not text:
            text = "empty"
        # Deterministic from hash
        seed = abs(hash(text)) % (2**32)
        vec = []
        for i in range(self.dimensions):
            val = ((seed + i * 31) % 10000) / 10000.0
            vec.append(val)
        return vec

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._fake_vector(t) for t in texts]


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """OpenAI-compatible embeddings (e.g. OpenAI, local vLLM, Ollama, LM Studio).
    Uses /v1/embeddings endpoint.
    Configured via env (see .env.example).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
    ):
        self.base_url = (base_url or AI_EMBEDDING_BASE_URL or "").rstrip("/")
        self.api_key = api_key or AI_EMBEDDING_API_KEY or ""
        self.model = model or AI_EMBEDDING_MODEL or "text-embedding-3-small"
        self.dimensions = dimensions or AI_EMBEDDING_DIMENSIONS

        if not self.base_url:
            raise ValueError("AI_EMBEDDING_BASE_URL must be set for openai_compatible provider")

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.model,
            "input": texts,
            # dimensions can be passed if supported by backend
            # "dimensions": self.dimensions,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, json=payload, headers=self._get_headers())
                resp.raise_for_status()
                data = resp.json()
                embeddings = [item["embedding"] for item in data.get("data", [])]
                # truncate or pad if needed to match configured dim (some backends ignore)
                for i, emb in enumerate(embeddings):
                    if len(emb) > self.dimensions:
                        embeddings[i] = emb[: self.dimensions]
                    elif len(emb) < self.dimensions:
                        embeddings[i] = emb + [0.0] * (self.dimensions - len(emb))
                return embeddings
        except Exception as exc:
            # In production, log properly. For MVP raise with context.
            raise RuntimeError(f"Embedding call to {url} failed: {exc}") from exc


def get_embedding_provider() -> EmbeddingProvider:
    """Factory based on AI_EMBEDDING_PROVIDER env."""
    provider = (AI_EMBEDDING_PROVIDER or "fake").lower()
    if provider in ("fake", "test", "deterministic"):
        return FakeEmbeddingProvider()
    elif provider in ("openai_compatible", "openai", "vllm", "ollama", "lmstudio"):
        return OpenAICompatibleEmbeddingProvider()
    else:
        # Default to fake for safety in dev
        return FakeEmbeddingProvider()
