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

    # ---- assistant (AvalAI) --------------------------------------------
    # Optional on purpose: without a key the panel still runs and only the
    # chat tab is disabled. Making it required would mean a missing key
    # refuses to boot the whole API over one feature.
    avalai_api_key: str | None = None
    avalai_base_url: str = "https://api.avalai.ir/v1"
    # Resolved from GET {avalai_base_url}/models at setup. AvalAI is a gateway
    # with its own catalogue naming, so upstream ids must not be hardcoded.
    avalai_model: str = ""

    @property
    def assistant_enabled(self) -> bool:
        return bool(self.avalai_api_key and self.avalai_model)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
