from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class PageType(str, Enum):
    CERTIFICATION = "certification"
    LEARNING_PATH = "learning_path"
    MODULE = "module"
    UNIT = "unit"
