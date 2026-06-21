import time

import strawberry

from app.graphql_api.types.types import CacheTestPayload, Response

CACHE_KEY = "poc:test_value"
CACHE_TTL = 60  # seconds


@strawberry.type
class CacheTestQueries:
    @strawberry.field
    def cache_ping(self, info: strawberry.types.Info) -> Response[str]:
        cache = info.context.cache
        if cache is None:
            return Response(success=False, message="Redis not configured")
        return Response(data="ok" if cache.ping() else "unavailable")

    @strawberry.field
    def cache_test(self, info: strawberry.types.Info) -> Response[CacheTestPayload]:
        cache = info.context.cache
        if cache is None:
            return Response(success=False, message="Redis not configured")

        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return Response(
                message="Cache hit",
                data=CacheTestPayload(
                    source="cache",
                    computed_at=cached["computed_at"],
                    payload=cached["payload"],
                    remaining_ttl=cache.ttl(CACHE_KEY),
                ),
            )

        value = {
            "computed_at": time.time(),
            "payload": "Simulated expensive computation result",
        }
        cache.set(CACHE_KEY, value, ttl=CACHE_TTL)
        return Response(
            message="Cache miss  -  value computed and stored",
            data=CacheTestPayload(
                source="computed",
                computed_at=value["computed_at"],
                payload=value["payload"],
                ttl=CACHE_TTL,
            ),
        )


@strawberry.type
class CacheTestMutations:
    @strawberry.mutation
    def clear_cache(self, info: strawberry.types.Info) -> Response[bool]:
        cache = info.context.cache
        if cache is None:
            return Response(success=False, message="Redis not configured")

        deleted = cache.delete(CACHE_KEY)
        return Response(
            message="Cache key deleted" if deleted else "Key was not in cache",
            data=deleted,
        )
