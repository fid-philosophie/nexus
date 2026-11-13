from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    allow_origins: list[str] = Field(default_factory=list)
    enable_custom_mappings: bool = False

    redis_url: str = "redis://redis:6379/0"

    api_contact_name: str = ""
    api_contact_email: str = ""

    http_user_agent: str = "NexusAPI/0.9"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()