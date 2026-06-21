import time

from fastapi import APIRouter, Request

from app.api.utils.utils import rest_api_response

router = APIRouter()

CACHE_KEY = "poc:test_value"
CACHE_TTL = 60  # seconds


@router.get("/cache/ping")
def cache_ping(request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        return rest_api_response(
            success=False, message="Redis not configured", status_code=503, request=request
        )
    return rest_api_response(
        data={"redis": "ok" if cache.ping() else "unavailable"}, request=request
    )


@router.get("/cache/test")
def cache_get(request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        return rest_api_response(
            success=False, message="Redis not configured", status_code=503, request=request
        )

    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return rest_api_response(
            message="Cache hit",
            data={**cached, "source": "cache", "remaining_ttl": cache.ttl(CACHE_KEY)},
            request=request,
        )

    value = {
        "computed_at": time.time(),
        "payload": "Simulated expensive computation result",
    }
    cache.set(CACHE_KEY, value, ttl=CACHE_TTL)
    return rest_api_response(
        message="Cache miss  -  value computed and stored",
        data={**value, "source": "computed", "ttl": CACHE_TTL},
        request=request,
    )


@router.delete("/cache/test")
def cache_invalidate(request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        return rest_api_response(
            success=False, message="Redis not configured", status_code=503, request=request
        )

    deleted = cache.delete(CACHE_KEY)
    return rest_api_response(
        message="Cache key deleted" if deleted else "Key was not in cache",
        data={"deleted": deleted},
        request=request,
    )
