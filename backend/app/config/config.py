from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CertificationInfo:
    SUPPORTED: dict[str, dict[str, str]] = {
        "az-204": {
            "title": "Azure Developer Associate",
            "description": "Build end-to-end solutions in Microsoft Azure to create Azure Functions, implement and manage web apps, develop solutions utilizing Azure storage, and more.",
            "study_guide_path": "/credentials/certifications/resources/study-guides/az-204",
            "cert_page_path": "/credentials/certifications/azure-developer/",
        },
        "az-104": {
            "title": "Azure Administrator Associate",
            "description": "Demonstrate key skills to configure, manage, secure, and administer key professional functions in Microsoft Azure.",
            "study_guide_path": "/credentials/certifications/resources/study-guides/az-104",
            "cert_page_path": "/credentials/certifications/azure-administrator/",
        },
        "az-900": {
            "title": "Azure Fundamentals",
            "description": "Demonstrate foundational knowledge of cloud concepts, core Azure services, plus Azure management and governance features and tools.",
            "study_guide_path": "/credentials/certifications/resources/study-guides/az-900",
            "cert_page_path": "/credentials/certifications/azure-fundamentals/",
            "course_path": "/training/courses/az-900t00"
        },
    }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ms_learn_base_url: str = "https://learn.microsoft.com/en-us"
    output_dir: Path = Field(default=Path("output"))
    scrape_delay_seconds: float = 1.0
    max_concurrent_requests: int = 5
    log_level: str = "INFO"

    @property
    def supported_certifications(self) -> dict[str, dict[str, str]]:
        return CertificationInfo.SUPPORTED

    def get_cert_url(self, cert_id: str, path_type: str = "cert_page_path") -> str:
        cert = self.supported_certifications.get(cert_id)
        if cert is None:
            raise ValueError(f"Unsupported certification: {cert_id}")
        return f"{self.ms_learn_base_url}{cert[path_type]}"

    def get_course_url(self, cert_id: str) -> str:
        return self.get_cert_url(cert_id, "course_path")


@lru_cache
def get_settings() -> Settings:
    return Settings()
