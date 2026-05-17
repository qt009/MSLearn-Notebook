import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.domain.exceptions import ContentParsingError
from app.domain.models import ImageRef, UnitContent

logger = logging.getLogger(__name__)

MS_LEARN_BASE = "https://learn.microsoft.com"


def _make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _resolve_url(relative: str, base: str = MS_LEARN_BASE) -> str:
    if relative.startswith("http"):
        return relative
    return urljoin(base, relative)


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


class LearningPathExtractor:
    def extract(self, html: str, base_url: str) -> list[dict[str, str]]:
        soup = _make_soup(html)
        paths: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = str(link["href"])
            if "/training/paths/" not in href:
                continue

            url = _resolve_url(href)
            normalized = url.split("?")[0].rstrip("/")
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)

            title = link.get_text(strip=True)
            if not title:
                continue

            paths.append({
                "title": title,
                "url": url,
                "slug": _slugify(title),
            })

        if not paths:
            logger.warning("No learning paths found on page: %s", base_url)

        return paths


class ModuleExtractor:
    def extract(self, html: str, base_url: str) -> list[dict[str, str]]:
        soup = _make_soup(html)
        modules: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for link in soup.find_all("a", href=True):
            href = str(link["href"])
            if "/training/modules/" not in href:
                continue

            url = _resolve_url(href)
            normalized = url.split("?")[0].rstrip("/")
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)

            title = link.get_text(strip=True)
            if not title:
                continue

            modules.append({
                "title": title,
                "url": url,
                "slug": _slugify(title),
            })

        if not modules:
            logger.warning("No modules found on learning path: %s", base_url)

        return modules


class UnitExtractor:
    def extract(self, html: str, base_url: str) -> list[dict[str, str]]:
        soup = _make_soup(html)
        units: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        module_path = base_url.split("?")[0].rstrip("/")
        module_slug = module_path.split("/")[-1]

        for link in soup.find_all("a", href=True):
            href = str(link["href"])
            if f"/training/modules/{module_slug}/" not in href:
                continue

            url = _resolve_url(href)
            normalized = url.split("?")[0].rstrip("/")

            unit_part = normalized.split("/")[-1]
            if unit_part == module_slug:
                continue

            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)

            title = link.get_text(strip=True)
            if not title:
                continue

            units.append({
                "title": title,
                "url": url,
                "slug": _slugify(title),
            })

        if not units:
            logger.warning("No units found in module: %s", base_url)

        return units


class UnitPageParser:
    """Parses unit page HTML into structured content, stripping navigation chrome."""

    STRIP_SELECTORS = [
        "header", "footer", "nav",
        ".breadcrumbs", "#comments-section", ".page-metadata",
        ".feedback-section", '[role="navigation"]', '[role="banner"]',
        '[role="contentinfo"]', ".site-header", ".site-footer",
        "#ms--additional-resources", ".alert",
    ]

    CONTENT_SELECTORS = [
        "main", '[role="main"]', ".content",
        "#main-column", "#unit-inner-section",
    ]

    def parse_unit(self, html: str, url: str) -> UnitContent:
        soup = _make_soup(html)
        title = self._extract_title(soup)

        content_el = self._find_content(soup)
        if content_el is None:
            raise ContentParsingError(
                f"Could not find main content area on page", url=url
            )

        self._strip_chrome(content_el)
        code_blocks = self._extract_code_blocks(content_el)
        images = self._extract_images(content_el, url)
        self._resolve_urls(content_el, url)
        html_body = str(content_el)
        slug = url.split("?")[0].rstrip("/").split("/")[-1]

        return UnitContent(
            title=title,
            slug=_slugify(slug),
            url=url,
            html_body=html_body,
            code_blocks=code_blocks,
            images=images,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            return raw.split(" - ")[0].strip()

        return "Untitled"

    def _find_content(self, soup: BeautifulSoup) -> Tag | None:
        for selector in self.CONTENT_SELECTORS:
            el = soup.select_one(selector)
            if el and len(el.get_text(strip=True)) > 100:
                return el
        return None

    def _strip_chrome(self, content: Tag) -> None:
        for selector in self.STRIP_SELECTORS:
            for el in content.select(selector):
                el.decompose()

    def _extract_code_blocks(self, content: Tag) -> list[str]:
        blocks: list[str] = []
        for pre in content.find_all("pre"):
            code = pre.find("code")
            if code:
                blocks.append(code.get_text())
            else:
                blocks.append(pre.get_text())
        return blocks

    def _extract_images(self, content: Tag, base_url: str) -> list[ImageRef]:
        images: list[ImageRef] = []
        for img in content.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue
            images.append(ImageRef(
                src=_resolve_url(src, base_url),
                alt=img.get("alt", ""),
            ))
        return images

    def _resolve_urls(self, content: Tag, base_url: str) -> None:
        for tag in content.find_all(["a", "img", "source"]):
            for attr in ("href", "src"):
                val = tag.get(attr)
                if val and not val.startswith(("http", "data:", "#", "mailto:")):
                    tag[attr] = _resolve_url(val, base_url)
