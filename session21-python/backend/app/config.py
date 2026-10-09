from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HelpDesk API"
    app_version: str = "1.0.0"
    database_url: str = "postgresql+psycopg://helpdesk:helpdesk@localhost:5432/helpdesk"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
