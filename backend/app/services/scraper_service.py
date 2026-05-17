import logging
from datetime import datetime, timezone, timedelta
from functools import partial

from app.config import Settings
from app.domain.enums import JobStatus
from app.domain.exceptions import (
    CertificationNotFoundError,
    ScraperError,
)
from app.domain.models import Certification
from app.scraper.crawler import MSLearnCrawler
from app.services.job_tracker import JobTracker
from app.storage.file_store import FileContentRepository

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL = timedelta(hours=24)


class ScraperService:
    def __init__(
        self,
        settings: Settings,
        repository: FileContentRepository,
        job_tracker: JobTracker,
    ):
        self._settings = settings
        self._repository = repository
        self._job_tracker = job_tracker

    def list_certifications(self) -> list[dict[str, str]]:
        certs = []
        for cert_id, info in self._settings.supported_certifications.items():
            certs.append({
                "cert_id": cert_id,
                "title": info["title"],
                "description": info["description"],
            })
        return certs

    async def start_scrape(
        self,
        cert_id: str,
        force: bool = False,
    ) -> str:
        if cert_id not in self._settings.supported_certifications:
            raise CertificationNotFoundError(cert_id)

        if not force:
            last_scraped = await self._repository.get_last_scraped(cert_id)
            if last_scraped:
                age = datetime.now(timezone.utc) - last_scraped
                if age < DEFAULT_CACHE_TTL:
                    logger.info(
                        "Certification %s was scraped %s ago (< %s TTL), "
                        "returning cached data",
                        cert_id, age, DEFAULT_CACHE_TTL,
                    )
                    job_id = self._job_tracker.create_job(cert_id)
                    self._job_tracker.mark_completed(job_id)
                    return job_id

        job_id = self._job_tracker.create_job(cert_id)
        return job_id

    async def run_scrape(self, job_id: str, cert_id: str) -> None:
        """Execute the scraping pipeline as a background task."""
        try:
            self._job_tracker.mark_scraping(job_id)

            progress_cb = partial(
                self._job_tracker.update_progress, job_id
            )

            crawler = MSLearnCrawler(self._settings)
            certification = await crawler.crawl_certification(
                cert_id, on_progress=progress_cb
            )

            self._job_tracker.update_progress(
                job_id, "Saving", 0.95, "Writing to disk"
            )
            await self._repository.save_certification(certification)

            self._job_tracker.mark_completed(job_id)
            logger.info("Scrape job %s completed for %s", job_id, cert_id)

        except ScraperError as e:
            self._job_tracker.mark_failed(job_id, str(e))
            logger.error("Scrape job %s failed: %s", job_id, e)

        except Exception as e:
            self._job_tracker.mark_failed(job_id, f"Unexpected error: {e}")
            logger.exception("Scrape job %s failed unexpectedly", job_id)

    def get_job_status(self, job_id: str) -> dict | None:
        job = self._job_tracker.get_job(job_id)
        if job is None:
            return None

        return {
            "job_id": job.job_id,
            "cert_id": job.cert_id,
            "status": job.status.value,
            "progress": job.progress,
            "current_step": job.current_step,
            "detail": job.detail,
            "error": job.error,
            "created_at": job.created_at.isoformat(),
            "completed_at": (
                job.completed_at.isoformat() if job.completed_at else None
            ),
        }

    async def get_certification(self, cert_id: str) -> Certification | None:
        return await self._repository.load_certification(cert_id)
