"""
Web crawler for MS Learn certification content.

Traverses the 4-level hierarchy:
  Certification → Learning Paths → Modules → Units

Uses the Factory pattern for HTTP client selection (httpx by default)
and the Observer pattern for progress reporting. Respects rate limits
via asyncio.Semaphore and configurable delays.
"""
import asyncio
import logging
from typing import Callable

import httpx

from app.config.config import Settings
from app.domain.exceptions import (
    NetworkError,
    PageNotFoundError,
    RateLimitError,
    ContentParsingError,
)
from app.domain.models import (
    Certification,
    LearningPath,
    Module,
    UnitContent,
)
from app.scraper.parser import (
    LearningPathExtractor,
    ModuleExtractor,
    UnitExtractor,
    UnitPageParser,
)

logger = logging.getLogger(__name__)

# Type alias for progress callback (Observer pattern)
ProgressCallback = Callable[[str, float, str], None]


def _noop_progress(step: str, progress: float, detail: str = "") -> None:
    """Default no-op progress callback."""
    pass


class MSLearnCrawler:
    """
    Crawls MS Learn certification content hierarchically.

    Architecture notes:
    - Uses httpx.AsyncClient for HTTP (Factory: could be swapped for Playwright)
    - asyncio.Semaphore caps concurrent requests
    - Progress is reported via callback injection (Observer pattern)
    - All HTTP errors are wrapped in domain exceptions
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self._delay = settings.scrape_delay_seconds

        # Strategy instances
        self._path_extractor = LearningPathExtractor()
        self._module_extractor = ModuleExtractor()
        self._unit_extractor = UnitExtractor()
        self._unit_parser = UnitPageParser()

    async def crawl_certification(
        self,
        cert_id: str,
        on_progress: ProgressCallback = _noop_progress,
    ) -> Certification:
        """
        Crawl the full content hierarchy for a certification.

        Args:
            cert_id: certification identifier (e.g. "az-204")
            on_progress: callback for reporting progress

        Returns:
            Fully populated Certification model.

        Raises:
            CertificationNotFoundError: if cert_id is not supported
            ScraperError: if scraping fails
        """
        cert_info = self._settings.supported_certifications[cert_id]
        course_url = self._settings.get_course_url(cert_id)

        logger.info("Starting crawl for %s: %s", cert_id, cert_info["title"])
        on_progress("Initializing", 0.0, f"Starting scrape of {cert_id}")

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": "MSLearn-Notebook-Scraper/1.0 (Educational Tool)",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            # Step 1: Get learning path links
            on_progress("Discovering learning paths", 0.05, course_url)
            learning_paths = await self._discover_learning_paths(
                client, cert_id, course_url
            )

            # Step 2: For each learning path, discover modules and units
            total_paths = len(learning_paths)
            populated_paths: list[LearningPath] = []

            for i, path_info in enumerate(learning_paths):
                path_progress = 0.1 + (0.85 * i / max(total_paths, 1))
                on_progress(
                    "Scraping learning paths",
                    path_progress,
                    f"[{i+1}/{total_paths}] {path_info['title']}",
                )

                path = await self._crawl_learning_path(client, path_info)
                populated_paths.append(path)

            on_progress("Completed", 1.0, f"Scraped {total_paths} learning paths")

        return Certification(
            cert_id=cert_id,
            title=cert_info["title"],
            url=course_url,
            learning_paths=populated_paths,
        )

    async def _discover_learning_paths(
        self,
        client: httpx.AsyncClient,
        cert_id: str,
        cert_url: str,
    ) -> list[dict[str, str]]:
        """
        Discover learning path URLs from the certification page.

        Tries the cert page first, then the study guide as fallback.
        """
        # Try certification page
        html = await self._fetch(client, cert_url)
        paths = self._path_extractor.extract(html, cert_url)

        if not paths:
            # Fallback: try the study guide page (has more links)
            study_guide_url = self._settings.get_cert_url(
                cert_id, "study_guide_path"
            )
            logger.info(
                "No paths on cert page, trying study guide: %s",
                study_guide_url,
            )
            html = await self._fetch(client, study_guide_url)
            paths = self._path_extractor.extract(html, study_guide_url)

        logger.info("Discovered %d learning paths for %s", len(paths), cert_id)
        return paths

    async def _crawl_learning_path(
        self,
        client: httpx.AsyncClient,
        path_info: dict[str, str],
    ) -> LearningPath:
        """Crawl a single learning path: discover modules → crawl units."""
        url = path_info["url"]
        logger.info("Crawling learning path: %s", path_info["title"])

        html = await self._fetch(client, url)

        # Extract description from the page
        description = path_info.get("description", "")

        # Discover modules
        module_infos = self._module_extractor.extract(html, url)
        logger.info(
            "  Found %d modules in path: %s",
            len(module_infos),
            path_info["title"],
        )

        # Crawl each module
        modules: list[Module] = []
        for mod_info in module_infos:
            module = await self._crawl_module(client, mod_info)
            modules.append(module)

        return LearningPath(
            title=path_info["title"],
            slug=path_info["slug"],
            description=description,
            url=url,
            modules=modules,
        )

    async def _crawl_module(
        self,
        client: httpx.AsyncClient,
        mod_info: dict[str, str],
    ) -> Module:
        """Crawl a single module: discover units → parse each unit."""
        url = mod_info["url"]
        logger.info("  Crawling module: %s", mod_info["title"])

        html = await self._fetch(client, url)

        # Discover units
        unit_infos = self._unit_extractor.extract(html, url)
        logger.info(
            "    Found %d units in module: %s",
            len(unit_infos),
            mod_info["title"],
        )

        # Crawl units concurrently (bounded by semaphore)
        tasks = [
            self._crawl_unit(client, unit_info)
            for unit_info in unit_infos
        ]
        units = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed units (log but don't abort)
        valid_units: list[UnitContent] = []
        for unit_info, result in zip(unit_infos, units):
            if isinstance(result, Exception):
                logger.warning(
                    "    Failed to parse unit '%s': %s",
                    unit_info["title"],
                    result,
                )
            else:
                valid_units.append(result)

        return Module(
            title=mod_info["title"],
            slug=mod_info["slug"],
            url=url,
            units=valid_units,
        )

    async def _crawl_unit(
        self,
        client: httpx.AsyncClient,
        unit_info: dict[str, str],
    ) -> UnitContent:
        """Crawl and parse a single unit page."""
        url = unit_info["url"]
        logger.debug("    Crawling unit: %s", unit_info["title"])

        html = await self._fetch(client, url)

        try:
            return self._unit_parser.parse_unit(html, url)
        except ContentParsingError:
            raise
        except Exception as e:
            raise ContentParsingError(
                f"Failed to parse unit: {e}", url=url
            ) from e

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> str:
        """
        Fetch a URL with rate limiting and error handling.

        Uses asyncio.Semaphore to cap concurrent requests and adds a
        configurable delay between requests to be respectful to the server.
        """
        async with self._semaphore:
            try:
                response = await client.get(url)

                if response.status_code == 404:
                    raise PageNotFoundError(
                        f"Page not found: {url}", url=url
                    )
                if response.status_code == 429:
                    raise RateLimitError(
                        f"Rate limited by server: {url}", url=url
                    )
                response.raise_for_status()

                # Rate limit delay
                await asyncio.sleep(self._delay)

                return response.text

            except (PageNotFoundError, RateLimitError):
                raise
            except httpx.HTTPStatusError as e:
                raise NetworkError(
                    f"HTTP {e.response.status_code} for {url}", url=url
                ) from e
            except httpx.HTTPError as e:
                raise NetworkError(
                    f"Network error fetching {url}: {e}", url=url
                ) from e
