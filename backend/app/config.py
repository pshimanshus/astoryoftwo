import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_env_local() -> None:
    # Minimal .env.local loader (repo convention; no python-dotenv dependency).
    root = Path(__file__).resolve().parents[2]
    env = root / ".env.local"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    gemini_api_key: str
    data_dir: Path
    image_model: str = "gpt-image-1"
    gemini_model: str = "gemini-2.5-flash"
    image_size: str = "1024x1536"
    min_slides: int = 3
    max_slides: int = 5


def load_settings() -> Settings:
    _load_env_local()
    data_dir = Path(os.environ.get("ASTORY_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
        data_dir=data_dir,
    )


settings = load_settings()
