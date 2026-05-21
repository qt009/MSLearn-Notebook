class ScraperError(Exception):
    def __init__(self, message: str, url: str | None = None):
        self.url = url
        super().__init__(message)


class PageNotFoundError(ScraperError):
    pass


class RateLimitError(ScraperError):
    pass


class ContentParsingError(ScraperError):
    pass


class NetworkError(ScraperError):
    pass


class CertificationNotFoundError(Exception):
    def __init__(self, cert_id: str):
        self.cert_id = cert_id
        super().__init__(f"Certification not found: {cert_id}")


class JobNotFoundError(Exception):
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class StorageError(Exception):
    pass


class PDFGenerationError(Exception):
    pass
