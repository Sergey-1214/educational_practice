import hashlib
import json
import logging
from uuid import UUID

from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.db.redis import redis_client
from app.modules.search.schemas import SearchParams, SearchResponse


logger = logging.getLogger(__name__)


class SearchCacheRepository:
    def __init__(self, client: Redis = redis_client) -> None:
        self.client = client
        self.ttl_seconds = settings.search_cache_ttl_seconds

    async def get_search_response(self, key: str) -> SearchResponse | None:
        try:
            cached_value = await self.client.get(key)
        except RedisError:
            logger.exception("Failed to read search response from Redis")
            return None

        if cached_value is None:
            return None

        try:
            return SearchResponse.model_validate_json(cached_value)
        except ValidationError:
            logger.exception("Invalid search response found in Redis cache")
            await self.delete_key(key)
            return None

    async def set_search_response(self, key: str, response: SearchResponse) -> None:
        try:
            await self.client.setex(
                key,
                self.ttl_seconds,
                response.model_dump_json(),
            )
        except RedisError:
            logger.exception("Failed to save search response to Redis")

    async def delete_user_search_cache(self, user_id: UUID) -> None:
        pattern = f"search:{user_id}:*"

        try:
            keys = [key async for key in self.client.scan_iter(match=pattern)]
            if keys:
                await self.client.delete(*keys)
        except RedisError:
            logger.exception("Failed to delete user search cache from Redis")

    async def delete_key(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except RedisError:
            logger.exception("Failed to delete invalid search cache key from Redis")


def build_search_cache_key(user_id: UUID, params: SearchParams) -> str:
    payload = {
        "user_id": str(user_id),
        "query": params.query,
        "document_id": str(params.document_id) if params.document_id else None,
        "limit": params.limit,
        "offset": params.offset,
    }
    raw_key = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"search:{user_id}:{digest}"
