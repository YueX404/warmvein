"""
Application settings loaded from environment variables.

Precedence: environment variable > .env file > default value.
"""

import logging
import os
from pathlib import Path

# Load .env if present (no extra dependency needed)
_env_path = Path(__file__).resolve().parents[3] / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        _k, _v = _k.strip(), _v.strip()
        if len(_v) >= 2 and _v[0] == _v[-1] and _v[0] in ("'", '"'):
            _v = _v[1:-1]
        else:
            # Strip inline comments: KEY=value  # comment
            _v = _v.split("#", 1)[0].strip()
        os.environ.setdefault(_k, _v)


class _Settings:
    """Read-only settings proxy — access via ``settings.FIELD``."""

    # FastAPI
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "dev-secret-key")
    APP_CORS_ORIGINS: str = os.getenv("APP_CORS_ORIGINS", "*")

    # MySQL
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "warmvein")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "warmvein123")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "warmvein")

    @property
    def DB_URL(self) -> str:  # noqa: N802
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    @property
    def REDIS_URL(self) -> str:  # noqa: N802
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    # SMS
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "local")

    # ML Model
    MODEL_DIR: str = os.getenv("MODEL_DIR", "models")

    # Climate compensation defaults (Ansai district)
    CLIMATE_TN: float = float(os.getenv("CLIMATE_TN", "18.0"))
    CLIMATE_TG_D: float = float(os.getenv("CLIMATE_TG_D", "75.0"))
    CLIMATE_TW_D: float = float(os.getenv("CLIMATE_TW_D", "-9.0"))
    CLIMATE_DT_D: float = float(os.getenv("CLIMATE_DT_D", "25.0"))


settings = _Settings()

if settings.APP_ENV.lower() not in ("development", "dev"):
    if not os.getenv("APP_SECRET_KEY"):
        logging.getLogger(__name__).critical(
            "APP_SECRET_KEY 未设置，正在使用内置默认值 — 生产环境必须通过环境变量配置"
        )
    if not os.getenv("MYSQL_PASSWORD"):
        logging.getLogger(__name__).critical(
            "MYSQL_PASSWORD 未设置，正在使用内置默认值 — 生产环境必须通过环境变量配置"
        )
