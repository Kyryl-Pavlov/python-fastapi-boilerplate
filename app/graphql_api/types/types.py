from typing import Generic, TypeVar

import strawberry
from strawberry.scalars import JSON  # noqa: F401  -  re-exported for resolvers

T = TypeVar("T")


@strawberry.type
class Response(Generic[T]):  # noqa: UP046
    success: bool = True
    message: str = ""
    data: T | None = None
    exc: strawberry.Private[BaseException | None] = None

    def __post_init__(self):
        # Log via context when available; context is not accessible here so
        # per-response logging is handled by the AppLogger in each resolver
        # or the request middleware in app/__init__.py.
        pass


@strawberry.type
class HealthStatus:
    version: str


@strawberry.type
class AuthPayload:
    access_token: str
    refresh_token: str | None = None


@strawberry.type
class MediaPayload:
    media_id: str
    url: str
    expires_in: int


@strawberry.type
class CacheTestPayload:
    source: str  # "cache" | "computed"
    computed_at: float
    payload: str
    ttl: int | None = None
    remaining_ttl: int | None = None


@strawberry.type
class EventPayload:
    id: str
    sqs_message_id: str
    type: str
    payload: JSON | None = None
    status: str
    created_at: str
    processed_at: str | None = None
