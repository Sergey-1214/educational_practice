from typing import Any

from elasticsearch import AsyncElasticsearch

from app.core.config import settings
from app.db.elasticsearch import elasticsearch_client


class ElasticsearchRepository:
    def __init__(self, client: AsyncElasticsearch = elasticsearch_client) -> None:
        self.client = client
        self.index_name = settings.elasticsearch_documents_index

    async def ensure_documents_index(self) -> None:
        exists = await self.client.indices.exists(index=self.index_name)
        if exists:
            return

        await self.client.indices.create(
            index=self.index_name,
            settings={
                "analysis": {
                    "filter": {
                        "russian_stop": {
                            "type": "stop",
                            "stopwords": "_russian_",
                        },
                        "russian_stemmer": {
                            "type": "stemmer",
                            "language": "russian",
                        },
                    },
                    "analyzer": {
                        "ru_analyzer": {
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "russian_stop",
                                "russian_stemmer",
                            ],
                        },
                    },
                },
            },
            mappings={
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "file_name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "page_number": {"type": "integer"},
                    "chunk_number": {"type": "integer"},
                    "text": {"type": "text", "analyzer": "ru_analyzer"},
                },
            },
        )

    async def index_document_chunks(
        self,
        chunks: list[dict[str, Any]],
    ) -> None:
        if not chunks:
            return

        await self.ensure_documents_index()
        operations: list[dict[str, Any]] = []
        for chunk in chunks:
            operations.append(
                {
                    "index": {
                        "_index": self.index_name,
                        "_id": chunk["chunk_id"],
                    },
                },
            )
            operations.append(chunk)

        response = await self.client.bulk(operations=operations, refresh=True)
        if response.get("errors"):
            raise RuntimeError("Failed to index document chunks")

    async def search_documents(
        self,
        query: str,
        document_id: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        await self.ensure_documents_index()
        return await self.client.search(
            index=self.index_name,
            query=self._build_search_query(query, document_id),
            highlight={
                "fields": {
                    "text": {
                        "pre_tags": ["<mark>"],
                        "post_tags": ["</mark>"],
                    },
                },
            },
            from_=offset,
            size=limit,
        )

    @staticmethod
    def _build_search_query(
        query: str,
        document_id: str | None,
    ) -> dict[str, Any]:
        text_query = {
            "multi_match": {
                "query": query,
                "fields": ["text"],
            },
        }
        if document_id is None:
            return text_query

        return {
            "bool": {
                "must": [text_query],
                "filter": [
                    {
                        "term": {
                            "document_id": document_id,
                        },
                    },
                ],
            },
        }
