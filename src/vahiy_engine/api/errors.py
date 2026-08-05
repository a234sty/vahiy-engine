"""Uniform JSON error handling for the API."""

from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from vahiy_engine.providers.llm.base import LLMProviderError


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


async def llm_provider_error_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"error": str(exc)})


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
