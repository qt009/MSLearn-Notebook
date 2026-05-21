from app.TrackerService.domain.enums import JobStatus
from pydantic import BaseModel, Field
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