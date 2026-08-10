from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from the environment.

    Every field without a default is required — the app refuses to start
    rather than fall back to an insecure value.
    """

    project_name: str = "Dental Clinic BI API"
    api_prefix: str = "/api"

    mongo_url: str
    mongo_db: str = "dental_clinic"

    # 32 hex chars minimum. A short secret makes the session signature
    # brute-forceable, so this is enforced rather than warned about.
    session_secret: str = Field(min_length=32)
    session_ttl_hours: int = 8

    # The Vite dev server. In production the frontend is served from the same
    # origin by nginx, so this list is empty and CORS never applies.
    cors_origins: list[str] = ["http://localhost:5173"]

    # Cookies are only marked Secure over HTTPS; leave false for local http.
    cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
