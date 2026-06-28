import uuid

import strawberry
from strawberry.file_uploads import Upload

from app.graphql_api.types.types import MediaPayload, Response
from app.security import get_token_from_bearer, verify_access_token
from app.services.aws_s3_service import get_presigned_url, upload_file

_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "mp4", "mov"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in _ALLOWED_EXTENSIONS


@strawberry.type
class MediaQueries:
    @strawberry.field
    def signed_url(self, media_id: str, info: strawberry.types.Info) -> Response[str]:
        auth_header = info.context.request.headers.get("Authorization", "")
        try:
            token = get_token_from_bearer(auth_header)
            user_id = verify_access_token(token)
        except Exception as e:
            return Response(success=False, message="Unauthorized", exc=e)

        from app.models.media import Media

        db = info.context.db
        try:
            record = db.get(Media, uuid.UUID(media_id))
        except ValueError as e:
            return Response(success=False, message="Invalid media ID", exc=e)

        if not record or str(record.user_id) != user_id:
            return Response(success=False, message="Not found")

        try:
            return Response(
                success=True, message="ok", data=get_presigned_url(record.content_key)
            )
        except Exception as e:
            return Response(success=False, message="Failed to generate URL", exc=e)


@strawberry.type
class MediaMutations:
    @strawberry.mutation
    def upload_file(
        self, file: Upload, info: strawberry.types.Info
    ) -> Response[MediaPayload]:
        auth_header = info.context.request.headers.get("Authorization", "")
        try:
            token = get_token_from_bearer(auth_header)
            user_id = verify_access_token(token)
        except Exception as e:
            return Response(success=False, message="Unauthorized", exc=e)

        if not file.filename or not _allowed_file(file.filename):
            allowed = ", ".join(sorted(_ALLOWED_EXTENSIONS))
            return Response(
                success=False,
                message=f"File type not allowed. Permitted: {allowed}",
            )

        try:
            s3_key = upload_file(file.file, user_id, file.filename)
        except Exception as e:
            return Response(success=False, message="File upload failed", exc=e)

        from app.models.media import Media

        db = info.context.db
        try:
            record = Media(user_id=uuid.UUID(user_id), content_key=s3_key)
            db.add(record)
            db.commit()
        except Exception as e:
            db.rollback()
            return Response(success=False, message="Failed to save file record", exc=e)

        try:
            signed_url = get_presigned_url(s3_key)
        except Exception as e:
            return Response(success=False, message="Failed to generate URL", exc=e)

        return Response(
            data=MediaPayload(
                media_id=str(record.id),
                url=signed_url,
                expires_in=info.context.presigned_url_expiry,
            ),
        )
