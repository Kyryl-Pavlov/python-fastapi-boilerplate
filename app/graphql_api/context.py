from typing import TYPE_CHECKING, Any

from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.logging.logger import AppLogger
    from app.services.cache_service import CacheService


class GraphQLContext(BaseContext):
    def __init__(
        self,
        db: "Session",
        cache: "CacheService | None" = None,
        logger_adapter: "AppLogger | None" = None,
        presigned_url_expiry: int = 86400,
    ) -> None:
        super().__init__()
        self.db = db
        self.cache = cache
        self.logger_adapter = logger_adapter
        self.presigned_url_expiry = presigned_url_expiry
