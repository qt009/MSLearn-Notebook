import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import get_settings
from app.domain.exceptions import (
    CertificationNotFoundError,
    JobNotFoundError,
    ScraperError,
    StorageError,
)


def _setup_logging() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_logging()
    logger = logging.getLogger(__name__)

    settings = get_settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("MSLearn-Notebook API starting up")
    logger.info("Output directory: %s", settings.output_dir.resolve())
    logger.info(
        "Supported certifications: %s",
        list(settings.supported_certifications.keys()),
    )

    yield

    logger.info("MSLearn-Notebook API shutting down")


app = FastAPI(
    title="MSLearn-Notebook API",
    description="Scrape Microsoft Learn certification paths and generate PDF study notebooks.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CertificationNotFoundError)
async def certification_not_found_handler(
    request: Request, exc: CertificationNotFoundError
):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "cert_id": exc.cert_id},
    )


@app.exception_handler(JobNotFoundError)
async def job_not_found_handler(
    request: Request, exc: JobNotFoundError
):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "job_id": exc.job_id},
    )


@app.exception_handler(ScraperError)
async def scraper_error_handler(
    request: Request, exc: ScraperError
):
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc), "url": exc.url},
    )


@app.exception_handler(StorageError)
async def storage_error_handler(
    request: Request, exc: StorageError
):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


app.include_router(router)
