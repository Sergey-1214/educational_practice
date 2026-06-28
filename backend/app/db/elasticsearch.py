from elasticsearch import AsyncElasticsearch

from app.core.config import settings


elasticsearch_client = AsyncElasticsearch(settings.elasticsearch_url)


async def close_elasticsearch() -> None:
    await elasticsearch_client.close()
