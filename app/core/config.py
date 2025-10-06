from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "sereia-tattoo-api"
    API: str = "/api"
    DATABASE_URL: str = "sqlite:///./app.db"

    SECRET_KEY: SecretStr | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def _require_secret(cls, value: SecretStr | None) -> SecretStr:
        if value is None or not value.get_secret_value():
            raise ValueError("SECRET_KEY must be set via .env")
        return value


settings = Settings()
