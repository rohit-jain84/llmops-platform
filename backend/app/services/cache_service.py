import logging
import time
import uuid
from datetime import datetime, timezone

from app.config import settings
from app.telemetry.metrics import get_metrics

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self._qdrant_client = None
        self._embedding_model = None

    def _get_qdrant_client(self):
        if self._qdrant_client is None:
            from qdrant_client import QdrantClient
            self._qdrant_client = QdrantClient(url=settings.qdrant_url)
        return self._qdrant_client

    def _get_embedding_model(self):
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._embedding_model

    def _collection_name(self, app_id: uuid.UUID) -> str:
        return f"cache_{str(app_id).replace('-', '_')}"

    def _ensure_collection(self, app_id: uuid.UUID):
        client = self._get_qdrant_client()
        collection_name = self._collection_name(app_id)
        try:
            client.get_collection(collection_name)
        except Exception:
            from qdrant_client.models import Distance, VectorParams
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def _embed(self, text: str) -> list[float]:
        model = self._get_embedding_model()
        return model.encode(text).tolist()

    async def lookup(self, app_id: uuid.UUID, query: str) -> dict | None:
        try:
            self._ensure_collection(app_id)
            client = self._get_qdrant_client()
            embedding = self._embed(query)

            results = client.search(
                collection_name=self._collection_name(app_id),
                query_vector=embedding,
                limit=1,
                score_threshold=settings.cache_similarity_threshold,
            )

            if results:
                hit = results[0]
                payload = hit.payload or {}
                # Check TTL
                created_at = payload.get("created_at", 0)
                ttl = payload.get("ttl_seconds", settings.cache_ttl_seconds)
                if time.time() - created_at < ttl:
                    get_metrics()["cache_hits"].add(1, {"result": "hit"})
                    return {
                        "response": payload.get("response", ""),
                        "model": payload.get("model", ""),
                        "prompt_version_id": payload.get("prompt_version_id"),
                    }
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")

        get_metrics()["cache_hits"].add(1, {"result": "miss"})
        return None

    async def store(
        self,
        app_id: uuid.UUID,
        query: str,
        response: str,
        model: str,
        prompt_version_id: str | None = None,
    ):
        try:
            self._ensure_collection(app_id)
            client = self._get_qdrant_client()
            embedding = self._embed(query)

            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "response": response,
                    "model": model,
                    "prompt_version_id": prompt_version_id,
                    "created_at": time.time(),
                    "ttl_seconds": settings.cache_ttl_seconds,
                },
            )
            client.upsert(
                collection_name=self._collection_name(app_id),
                points=[point],
            )
        except Exception as e:
            logger.warning(f"Cache store failed: {e}")
