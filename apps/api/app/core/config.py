"""Local-only configuration. Environment values are never logged."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Settings:
    database_path: Path = field(default_factory=lambda: Path(os.getenv(
        "CIVICPLAIN_DATABASE_PATH") or str(ROOT / "data/tmp/civicplain.sqlite3")))
    allowed_origins: tuple[str, ...] = field(default_factory=lambda: tuple(
        origin.strip() for origin in (os.getenv(
            "CIVICPLAIN_ALLOWED_ORIGINS") or "http://127.0.0.1:5173,http://localhost:5173"
        ).split(",") if origin.strip()))

    def __post_init__(self):
        for origin in self.allowed_origins:
            parsed = urlparse(origin)
            if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"}
                    or parsed.path or parsed.query or parsed.fragment or parsed.username
                    or parsed.password or not parsed.port):
                raise ValueError("CORS origins must be explicit local HTTP origins with ports")
