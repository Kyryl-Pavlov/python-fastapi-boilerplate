from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.utils.utils import rest_api_response
from app.database import get_db
from app.models.event import Event
from app.security import require_access_token
from app.services.aws_sqs_service import send_event

router = APIRouter()


class PublishRequest(BaseModel):
    type: str
    payload: dict | None = None


@router.post("", status_code=202)
def publish(
    body: PublishRequest,
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_access_token),
):
    event_type = body.type.strip()
    if not event_type:
        return rest_api_response(
            success=False,
            message="Event type is required",
            status_code=400,
            request=request,
        )

    try:
        message_id = send_event(event_type, body.payload or {})
    except Exception as e:
        return rest_api_response(
            success=False,
            message="Failed to publish event",
            status_code=500,
            exc=e,
            request=request,
        )

    return rest_api_response(
        data={"message_id": message_id}, status_code=202, request=request
    )


@router.get("")
def list_events(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_access_token),
):
    try:
        rows = db.query(Event).order_by(Event.created_at.desc()).limit(100).all()
    except Exception as e:
        return rest_api_response(
            success=False,
            message="Failed to fetch events",
            status_code=500,
            exc=e,
            request=request,
        )

    return rest_api_response(
        data=[
            {
                "id": str(r.id),
                "sqs_message_id": r.sqs_message_id,
                "type": r.type,
                "payload": r.payload,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
            }
            for r in rows
        ],
        request=request,
    )
