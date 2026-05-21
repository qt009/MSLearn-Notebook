import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.api.helper.dependencies import get_scraper_service
from app.core.model.schemas import (
    CertificationListResponse,
    CertificationResponse,
)

from app.ScraperService.model.scrape import (
    ScrapeRequest,
    ScrapeStartResponse
)
from app.TrackerService.model.job import JobResponse

from app.core.domain.exceptions import CertificationNotFoundError, JobNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["MSLearn Notebook"])


@router.get("/certifications", response_model=CertificationListResponse)
async def list_certifications():
    service = get_scraper_service()
    certs = service.list_certifications()

    return CertificationListResponse(
        certifications=[
            CertificationResponse(**c) for c in certs
        ],
        count=len(certs),
    )


@router.post("/scrape/{cert_id}", response_model=ScrapeStartResponse)
async def start_scrape(
    cert_id: str,
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
):
    """Start an async scrape job. Returns a job_id immediately — poll GET /api/jobs/{job_id} for progress."""
    service = get_scraper_service()

    try:
        job_id = await service.start_scrape(
            cert_id=cert_id,
            force=request.force,
        )
    except CertificationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    status = service.get_job_status(job_id)
    if status and status["status"] == "completed":
        return ScrapeStartResponse(
            job_id=job_id,
            message=f"Cached data available for {cert_id}. No scraping needed.",
        )

    background_tasks.add_task(service.run_scrape, job_id, cert_id)

    return ScrapeStartResponse(
        job_id=job_id,
        message=f"Scrape job started for {cert_id}. Poll /api/jobs/{job_id} for progress.",
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    service = get_scraper_service()
    status = service.get_job_status(job_id)

    if status is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobResponse(**status)


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "mslearn-notebook-api"}
