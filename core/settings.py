from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        validate_default=False,
        env_ignore_empty=True,
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    PORT: int
    HOST: str
    DATABASE_URL: str
    TEST_SECRET: str
    TEST_HASH: str
    ALGORITHM: str
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    MRA_EIS_URL: str
    MRA_EIS_TIMEOUT: int = 30
    APP_NAME: str
    APP_VERSION: str

settings = Settings()