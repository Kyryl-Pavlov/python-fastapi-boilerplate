import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

REST_API_VN = os.environ.get("REST_API_VN", "1.0.0")


@router.get("/health")
def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": REST_API_VN})
