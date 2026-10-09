from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.routes.certificates import router as certificates_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.core.config import settings
from app.core.logging import logger
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    logger.info("Starting up %s (v%s)...", settings.APP_NAME, settings.APP_VERSION)
    # Ensure database tables exist
    init_db()
    # Ensure certificate storage directory exists
    _ = settings.storage_path
    logger.info("Initialized database and storage at %s", settings.STORAGE_DIR)
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="High-performance, production-quality bulk certificate generation backend API.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Exception handlers for clean API responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors into clear, actionable responses."""
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", [])])
        errors.append({
            "field": field,
            "message": err.get("msg"),
            "type": err.get("type")
        })
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "The submitted payload failed validation.",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server exceptions without leaking internal stack traces."""
    logger.exception("Unhandled server error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected server error occurred. Please try again later."
        }
    )


# Include API Routers
app.include_router(health_router)
app.include_router(jobs_router, prefix=settings.API_V1_STR)
app.include_router(certificates_router, prefix=settings.API_V1_STR)
