from datetime import UTC, datetime
from uuid import UUID, uuid4

import bcrypt
from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    def set_password(self, password: str) -> None:
        # rounds=13 makes hashing ~600 ms; default 12 is ~300 ms
        self.password_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt(rounds=13)
        ).decode()

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())
