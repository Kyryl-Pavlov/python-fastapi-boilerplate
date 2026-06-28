import strawberry

from app.graphql_api.types.types import AuthPayload, Response
from app.security import (
    create_access_token,
    create_refresh_token,
    get_token_from_bearer,
    verify_refresh_token,
)


@strawberry.type
class AuthMutations:
    @strawberry.mutation
    def register(
        self, email: str, password: str, info: strawberry.types.Info
    ) -> Response[str]:
        db = info.context.db
        email = email.strip().lower()
        if not email or not password:
            return Response(success=False, message="Email and password are required")

        from app.models.user import User

        if db.query(User).filter_by(email=email).first():
            return Response(success=False, message="Email already registered")

        try:
            user = User(email=email)
            user.set_password(password)
            db.add(user)
            db.commit()
        except Exception as e:
            db.rollback()
            return Response(success=False, message="Registration failed", exc=e)

        return Response()

    @strawberry.mutation
    def login(
        self, email: str, password: str, info: strawberry.types.Info
    ) -> Response[AuthPayload]:
        db = info.context.db
        from app.models.user import User

        try:
            user = db.query(User).filter_by(email=email.strip().lower()).first()
            if not user or not user.check_password(password):
                return Response(success=False, message="Invalid credentials")

            return Response(
                data=AuthPayload(
                    access_token=create_access_token(str(user.id)),
                    refresh_token=create_refresh_token(str(user.id)),
                )
            )
        except Exception as e:
            return Response(success=False, message="Login failed", exc=e)

    @strawberry.mutation
    def refresh_token(self, info: strawberry.types.Info) -> Response[AuthPayload]:
        auth_header = info.context.request.headers.get("Authorization", "")
        try:
            token = get_token_from_bearer(auth_header)
            user_id = verify_refresh_token(token)
        except Exception as e:
            return Response(
                success=False, message="Invalid or expired refresh token", exc=e
            )

        try:
            return Response(data=AuthPayload(access_token=create_access_token(user_id)))
        except Exception as e:
            return Response(success=False, message="Token refresh failed", exc=e)
