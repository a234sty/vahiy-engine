"""FastAPI application entrypoint for Vahiy Engine."""

from fastapi import FastAPI
from fastapi.exceptions import HTTPException

from vahiy_engine.api.errors import (
    http_exception_handler,
    llm_provider_error_handler,
    unhandled_exception_handler,
)
from vahiy_engine.api.routes import chat, health, search, verse
from vahiy_engine.config import settings
from vahiy_engine.logging import configure_logging
from vahiy_engine.providers.llm.base import LLMProviderError


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(LLMProviderError, llm_provider_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health.router)
    app.include_router(verse.router)
    app.include_router(search.router)
    app.include_router(chat.router)

    return app


app = create_app()
