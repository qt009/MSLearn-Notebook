from pydantic import BaseModel, Field

from app.domain.enums import JobStatus


class CertificationResponse(BaseModel):
    cert_id: str
    title: str
    description: str


class CertificationListResponse(BaseModel):
    certifications: list[CertificationResponse]
    count: int


class ScrapeRequest(BaseModel):
    force: bool = Field(
        default=False,
        description="If true, bypass cache and re-scrape even if recent data exists",
    )


class JobResponse(BaseModel):
    job_id: str
    cert_id: str
    status: JobStatus
    progress: float = Field(ge=0.0, le=1.0)
    current_step: str = ""
    detail: str = ""
    error: str | None = None
    created_at: str
    completed_at: str | None = None


class ScrapeStartResponse(BaseModel):
    job_id: str
    message: str
