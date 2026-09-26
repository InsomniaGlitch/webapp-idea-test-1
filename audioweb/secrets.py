from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


def load_dotenv(env_file: Path | str | None = None) -> None:
    """Load environment variables from a local .env file if present.

    Existing process environment values always win over file values, which keeps
    runtime secrets sourced from the deployment environment when available.
    """
    path = Path(env_file) if env_file is not None else ENV_FILE
    if not path.exists() or not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()

        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def get_secret(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    """Return a secret from the process environment, with optional validation."""
    value = os.environ.get(name)
    if value is None or (isinstance(value, str) and value.strip() == ""):
        value = default

    if value is None and required:
        raise RuntimeError(
            f"Missing required secret: {name}. Set it in the process environment or .env."
        )

    return value
