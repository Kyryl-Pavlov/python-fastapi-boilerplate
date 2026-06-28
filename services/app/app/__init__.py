import importlib
import os
import time

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from . import models  # noqa: F401  -  registers models with SQLAlchemy for migrations
from .config import config
from .database import init_db
from .graphql_api import create_graphql_router
from .logging.cloudwatch_logger import CloudWatchLogger
from .logging.logger import AppLogger, ConsoleLogger
from .logging.loki_logger import LokiLogger
from .services.cache_service import CacheService

REST_API_V = os.environ.get("REST_API_V", "v1")
api_module = importlib.import_module(f".api.{REST_API_V}", package=__name__)


def create_app(config_name: str | None = None) -> FastAPI:
    if config_name is None:
        config_name = os.environ.get("APP_ENV", "development")

    cfg = config.get(config_name, config["default"])

    app = FastAPI(
        title="FastAPI Boilerplate",
        debug=getattr(cfg, "DEBUG", False),
    )

    # ── Database ────────────────────────────────────────────────────────────
    init_db(cfg.DATABASE_URL)

    # ── Logging ─────────────────────────────────────────────────────────────
    loggers = [ConsoleLogger(debug=getattr(cfg, "DEBUG", False))]

    if cfg.SENTRY_DSN:
        from .logging.sentry_logger import SentryLogger

        loggers.append(SentryLogger(dsn=cfg.SENTRY_DSN, environment=config_name))

    if cfg.CLOUDWATCH_LOG_GROUP:
        try:
            loggers.append(
                CloudWatchLogger(
                    log_group=cfg.CLOUDWATCH_LOG_GROUP,
                    stream_name=cfg.CLOUDWATCH_STREAM_NAME,
                    region=cfg.AWS_DEFAULT_REGION,
                    aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
                    endpoint_url=cfg.CLOUDWATCH_ENDPOINT_URL,
                )
            )
        except Exception as e:
            import logging

            logging.warning(f"CloudWatch logger unavailable, skipping: {e}")

    if cfg.LOKI_URL:
        loggers.append(
            LokiLogger(
                url=cfg.LOKI_URL,
                labels={"app": "fastapi-boilerplate", "env": config_name},
            )
        )

    app.state.logger_adapter = AppLogger(*loggers)

    # ── Cache ────────────────────────────────────────────────────────────────
    app.state.cache = CacheService.from_url(cfg.REDIS_URL) if cfg.REDIS_URL else None

    # ── App state for resolvers / handlers ───────────────────────────────────
    app.state.presigned_url_expiry = cfg.PRESIGNED_URL_EXPIRY

    # ── Prometheus ───────────────────────────────────────────────────────────
    Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/metrics"],
    ).instrument(app).expose(app)

    # ── REST API ─────────────────────────────────────────────────────────────
    app.include_router(api_module.router, prefix=f"/api/{REST_API_V}")

    # ── GraphQL ──────────────────────────────────────────────────────────────
    introspection = getattr(cfg, "GRAPHQL_INTROSPECTION", False)
    graphql_router = create_graphql_router(introspection=introspection)
    app.include_router(graphql_router, prefix="/graphql")

    # ── Request timing middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def log_response_time(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        app.state.logger_adapter.log(
            "response",
            level=AppLogger.Level.INFO,
            data={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    return app
