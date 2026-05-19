import uuid
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field

from app.domain.enums import JobStatus

logger = logging.getLogger(__name__)


@dataclass
class JobInfo:
    job_id: str
    cert_id: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    current_step: str = ""
    detail: str = ""
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class JobTracker:
    """In-memory job state manager. Safe for single-process async; swap to Redis for multi-worker."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobInfo] = {}

    def create_job(self, cert_id: str) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobInfo(job_id=job_id, cert_id=cert_id)
        logger.info("Created job %s for cert %s", job_id, cert_id)
        return job_id

    def get_job(self, job_id: str) -> JobInfo | None:
        return self._jobs.get(job_id)

    def update_progress(
        self,
        job_id: str,
        step: str,
        progress: float,
        detail: str = "",
    ) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            logger.warning("Attempted to update unknown job: %s", job_id)
            return

        job.current_step = step
        job.progress = min(max(progress, 0.0), 1.0)
        job.detail = detail
        logger.debug(
            "Job %s progress: %.1f%% - %s - %s",
            job_id, progress * 100, step, detail,
        )

    def mark_status_scraping(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.SCRAPING

    def mark_status_generating(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.GENERATING

    def mark_status_completed(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            logger.info("Job %s completed", job_id)

    def mark_status_failed(self, job_id: str, error: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now(timezone.utc)
            logger.error("Job %s failed: %s", job_id, error)
