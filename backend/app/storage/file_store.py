import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.core.domain.exceptions import StorageError
from app.core.domain.models import Certification

logger = logging.getLogger(__name__)


class FileContentRepository:
    """
    Persists certification data to disk:
      tests/output/{cert_id}/metadata.json
      tests/output/{cert_id}/raw_html/path-{nn}/module-{nn}/unit-{nn}.html
    """

    def __init__(self, output_dir: Path):
        self._output_dir = output_dir

    def _cert_dir(self, cert_id: str) -> Path:
        return self._output_dir / cert_id

    def _metadata_path(self, cert_id: str) -> Path:
        return self._cert_dir(cert_id) / "metadata.json"

    def _raw_html_dir(self, cert_id: str) -> Path:
        return self._cert_dir(cert_id) / "raw_html"

    async def save_certification(self, cert: Certification) -> None:
        try:
            html_dir = self._raw_html_dir(cert.cert_id)
            html_dir.mkdir(parents=True, exist_ok=True)

            for p_idx, path in enumerate(cert.learning_paths):
                path_dir = html_dir / f"path-{p_idx+1:02d}_{path.slug}"
                path_dir.mkdir(parents=True, exist_ok=True)

                for m_idx, module in enumerate(path.modules):
                    mod_dir = path_dir / f"module-{m_idx+1:02d}_{module.slug}"
                    mod_dir.mkdir(parents=True, exist_ok=True)

                    for u_idx, unit in enumerate(module.units):
                        unit_file = mod_dir / f"unit-{u_idx+1:02d}_{unit.slug}.html"
                        unit_file.write_text(unit.html_body, encoding="utf-8")

            now = datetime.now(timezone.utc)
            cert_with_timestamp = cert.model_copy(update={"scraped_at": now})

            metadata = {
                "certification": cert_with_timestamp.model_dump(mode="json"),
                "scraped_at": now.isoformat(),
                "stats": {
                    "learning_paths": len(cert.learning_paths),
                    "total_modules": sum(
                        len(p.modules) for p in cert.learning_paths
                    ),
                    "total_units": sum(
                        len(m.units)
                        for p in cert.learning_paths
                        for m in p.modules
                    ),
                },
            }

            meta_path = self._metadata_path(cert.cert_id)
            meta_path.write_text(
                json.dumps(metadata, indent=2, default=str),
                encoding="utf-8",
            )

            logger.info(
                "Saved certification %s: %d paths, %d modules, %d units",
                cert.cert_id,
                metadata["stats"]["learning_paths"],
                metadata["stats"]["total_modules"],
                metadata["stats"]["total_units"],
            )

        except OSError as e:
            raise StorageError(f"Failed to save certification {cert.cert_id}: {e}") from e

    async def load_certification(self, cert_id: str) -> Certification | None:
        meta_path = self._metadata_path(cert_id)

        if not meta_path.exists():
            return None

        try:
            raw = json.loads(meta_path.read_text(encoding="utf-8"))
            return Certification.model_validate(raw["certification"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to load certification %s: %s", cert_id, e)
            return None

    async def has_certification(self, cert_id: str) -> bool:
        return self._metadata_path(cert_id).exists()

    async def get_last_scraped(self, cert_id: str) -> datetime | None:
        meta_path = self._metadata_path(cert_id)

        if not meta_path.exists():
            return None

        try:
            raw = json.loads(meta_path.read_text(encoding="utf-8"))
            ts = raw.get("scraped_at")
            if ts:
                return datetime.fromisoformat(ts)
            return None
        except (json.JSONDecodeError, ValueError):
            return None
