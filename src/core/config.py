from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Fiindo API
    FIINDO_API_BASE: str = Field(
        default="https://api.test.fiindo.com",
        description="Base URL for Fiindo API",
    )
    FIINDO_AUTH: str = Field(
        default="first.last",
        description="Fiindo auth identifier: first.last",
    )

    LOG_LEVEL: str = Field(default="INFO")

    # HTTP
    HTTP_TIMEOUT: int = Field(default=10)
    HTTP_RETRIES: int = Field(default=3)

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///fiindo_challenge.db"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()