from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.utils.utils import rest_api_response
from app.database import get_db
from app.models.user import User
from app.security import (
    create_access_token,
    create_refresh_token,
    require_refresh_token,
)

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=201)
def register(body: AuthRequest, request: Request, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    password = body.password

    if not email or not password:
        return rest_api_response(
            success=False,
            message="Email and password are required",
            status_code=400,
            request=request,
        )

    if db.query(User).filter_by(email=email).first():
        return rest_api_response(
            success=False,
            message="Email already registered",
            status_code=409,
            request=request,
        )

    try:
        user = User(email=email)
        user.set_password(password)
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        return rest_api_response(
            success=False,
            message="Registration failed",
            status_code=500,
            exc=e,
            request=request,
        )

    return rest_api_response(status_code=201, request=request)


@router.post("/login")
def login(body: AuthRequest, request: Request, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    password = body.password

    if not email or not password:
        return rest_api_response(
            success=False,
            message="Email and password are required",
            status_code=400,
            request=request,
        )

    try:
        user: User = db.query(User).filter_by(email=email).first()
        if not user or not user.check_password(password):
            return rest_api_response(
                success=False,
                message="Invalid credentials",
                status_code=401,
                request=request,
            )

        return rest_api_response(
            data={
                "access_token": create_access_token(str(user.id)),
                "refresh_token": create_refresh_token(str(user.id)),
            },
            request=request,
        )
    except Exception as e:
        return rest_api_response(
            success=False,
            message="Login failed",
            status_code=500,
            exc=e,
            request=request,
        )


@router.post("/refresh")
def refresh(
    request: Request,
    user_id: str = Depends(require_refresh_token),
):
    try:
        return rest_api_response(
            data={"access_token": create_access_token(user_id)},
            request=request,
        )
    except Exception as e:
        return rest_api_response(
            success=False,
            message="Token refresh failed",
            status_code=500,
            exc=e,
            request=request,
        )
