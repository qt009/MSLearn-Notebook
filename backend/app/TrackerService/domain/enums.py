from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"