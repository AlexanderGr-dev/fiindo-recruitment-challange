from typing import Annotated
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    # Fiindo API
    FIINDO_API_BASE: str = Field(
        default="https://api.test.fiindo.com",
        description="Base URL for Fiindo API",
    )
    FIINDO_AUTH: str = Field(
        default="first.last",
        description="Fiindo auth identifier: first.last",
    )

    ETL_MAX_WORKERS: Annotated[int, Field(le=10, ge=1)] = 8

    LOG_LEVEL: str = Field(default="INFO")

    # HTTP
    HTTP_TIMEOUT: int = Field(default=10)
    HTTP_RETRIES: int = Field(default=3,ge=2)

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///fiindo_challenge.db"
    )


settings = Settings()