from pydantic import BaseModel, Field

class ScrapeRequest(BaseModel):
    force: bool = Field(
        default=False,
        description="If true, bypass cache and re-scrape even if recent data exists",
    )

class ScrapeStartResponse(BaseModel):
    job_id: str
    message: str