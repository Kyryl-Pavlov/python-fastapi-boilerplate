from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.extensions import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    sqs_message_id: Mapped[str] = mapped_column(
        String(256), unique=True, nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="processed"
    )  # processed | failed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
