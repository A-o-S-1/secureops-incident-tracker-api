from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "SecureOps Incident Tracker API"
    environment: str = "development"
    database_url: str = "sqlite:///./secureops.db"
    secret_key: str
    access_token_expire_minutes: int = 30
    cors_origins: str = ""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
