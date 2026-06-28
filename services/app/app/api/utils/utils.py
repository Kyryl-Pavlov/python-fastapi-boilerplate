from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from app.logging.logger import AppLogger


def rest_api_response(
    success: bool = True,
    message: str = "",
    data: dict[str, Any] | list | None = None,
    status_code: int = 200,
    exc: BaseException | None = None,
    request: Request | None = None,
) -> JSONResponse:
    if data is None:
        data = {}

    if request is not None:
        logger = getattr(request.app.state, "logger_adapter", None)
        if logger is not None:
            if success:
                level = AppLogger.Level.INFO
            elif status_code >= 500:
                level = AppLogger.Level.ERROR
            else:
                level = AppLogger.Level.WARN
            logger.log(message, level=level, data=data or None, exc=exc)

    return JSONResponse(
        content={"success": success, "message": message, "data": data},
        status_code=status_code,
    )
