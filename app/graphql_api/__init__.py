from fastapi import Depends, Request
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from app.database import get_db

from .context import GraphQLContext
from .schema import schema


async def get_context(
    request: Request,
    db: Session = Depends(get_db),
) -> GraphQLContext:
    state = request.app.state
    return GraphQLContext(
        db=db,
        cache=getattr(state, "cache", None),
        logger_adapter=getattr(state, "logger_adapter", None),
        presigned_url_expiry=getattr(state, "presigned_url_expiry", 86400),
    )


def create_graphql_router(introspection: bool = False) -> GraphQLRouter:
    return GraphQLRouter(
        schema,
        context_getter=get_context,
        multipart_uploads_enabled=True,
        graphql_ide="graphiql" if introspection else None,
    )
