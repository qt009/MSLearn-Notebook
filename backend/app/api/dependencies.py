from functools import lru_cache

from app.config import Settings, get_settings
from app.services.job_tracker import JobTracker
from app.services.scraper_service import ScraperService
from app.storage.file_store import FileContentRepository

_job_tracker: JobTracker | None = None
_scraper_service: ScraperService | None = None


def get_job_tracker() -> JobTracker:
    global _job_tracker
    if _job_tracker is None:
        _job_tracker = JobTracker()
    return _job_tracker


def get_content_repository(
    settings: Settings | None = None,
) -> FileContentRepository:
    if settings is None:
        settings = get_settings()
    return FileContentRepository(output_dir=settings.output_dir)


def get_scraper_service(
    settings: Settings | None = None,
) -> ScraperService:
    global _scraper_service
    if _scraper_service is None:
        if settings is None:
            settings = get_settings()
        _scraper_service = ScraperService(
            settings=settings,
            repository=get_content_repository(settings),
            job_tracker=get_job_tracker(),
        )
    return _scraper_service
