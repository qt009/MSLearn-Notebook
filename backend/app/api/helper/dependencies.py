from functools import lru_cache

from app.config.config import get_settings
from app.services.job_tracker import JobTracker
from app.services.scraper_service import ScraperService
from app.storage.file_store import FileContentRepository


@lru_cache(maxsize=1)
def get_job_tracker() -> JobTracker:
    return JobTracker()


@lru_cache(maxsize=1)
def get_content_repository() -> FileContentRepository:
    return FileContentRepository(output_dir=get_settings().output_dir)


@lru_cache(maxsize=1)
def get_scraper_service() -> ScraperService:
    settings = get_settings()
    return ScraperService(
        settings=settings,
        repository=get_content_repository(),
        job_tracker=get_job_tracker(),
    )
