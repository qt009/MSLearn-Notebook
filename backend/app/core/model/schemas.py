from pydantic import BaseModel


class CertificationResponse(BaseModel):
    cert_id: str
    title: str
    description: str


class CertificationListResponse(BaseModel):
    certifications: list[CertificationResponse]
    count: int



