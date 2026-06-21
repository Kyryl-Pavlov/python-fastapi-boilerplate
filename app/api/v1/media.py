import uuid

from fastapi import APIRouter, Depends, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.utils.utils import rest_api_response
from app.database import get_db
from app.models.media import Media
from app.security import require_access_token
from app.services.aws_s3_service import get_presigned_url, upload_file

router = APIRouter()

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "mp4", "mov"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@router.post("/upload", status_code=201)
def upload(
    file: UploadFile,
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_access_token),
):
    if not file.filename:
        return rest_api_response(
            success=False, message="Empty filename", status_code=400, request=request
        )

    if not allowed_file(file.filename):
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return rest_api_response(
            success=False,
            message=f"File type not allowed. Permitted: {allowed}",
            status_code=415,
            request=request,
        )

    try:
        s3_key = upload_file(file.file, user_id, file.filename)
    except Exception as e:
        return rest_api_response(
            success=False,
            message="File upload failed",
            status_code=500,
            exc=e,
            request=request,
        )

    try:
        record = Media(user_id=uuid.UUID(user_id), content_key=s3_key)
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        return rest_api_response(
            success=False,
            message="Failed to save file record",
            status_code=500,
            exc=e,
            request=request,
        )

    try:
        signed_url = get_presigned_url(s3_key)
    except Exception as e:
        return rest_api_response(
            success=False,
            message="Failed to generate URL",
            status_code=500,
            exc=e,
            request=request,
        )

    return rest_api_response(
        data={"media_id": str(record.id), "url": signed_url, "expires_in": 3600},
        status_code=201,
        request=request,
    )


@router.get("/{media_id}/url")
def get_url(
    media_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_access_token),
):
    try:
        record = db.get(Media, uuid.UUID(media_id))
    except ValueError as e:
        return rest_api_response(
            success=False,
            message="Invalid media ID",
            status_code=400,
            exc=e,
            request=request,
        )

    if not record or str(record.user_id) != user_id:
        return rest_api_response(
            success=False, message="Not found", status_code=404, request=request
        )

    try:
        return rest_api_response(
            data={"url": get_presigned_url(record.content_key)}, request=request
        )
    except Exception as e:
        return rest_api_response(
            success=False,
            message="Failed to generate URL",
            status_code=500,
            exc=e,
            request=request,
        )
