from datetime import datetime

from pydantic import BaseModel, Field


class ImageRef(BaseModel):
    src: str
    alt: str = ""
    local_path: str | None = None


class UnitContent(BaseModel):
    title: str
    slug: str
    url: str
    html_body: str = ""
    code_blocks: list[str] = Field(default_factory=list)
    images: list[ImageRef] = Field(default_factory=list)


class Module(BaseModel):
    title: str
    slug: str
    url: str
    units: list[UnitContent] = Field(default_factory=list)


class LearningPath(BaseModel):
    title: str
    slug: str
    description: str = ""
    url: str
    modules: list[Module] = Field(default_factory=list)


class Certification(BaseModel):
    cert_id: str
    title: str
    url: str
    learning_paths: list[LearningPath] = Field(default_factory=list)
    scraped_at: datetime | None = None
