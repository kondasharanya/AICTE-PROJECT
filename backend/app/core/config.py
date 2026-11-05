"""
Core configuration – reads from .env via pydantic-settings.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── IBM watsonx.ai ─────────────────────────────────────────
    ibm_watsonx_api_key: str = Field("", env="IBM_WATSONX_API_KEY")
    ibm_watsonx_project_id: str = Field("", env="IBM_WATSONX_PROJECT_ID")
    ibm_watsonx_url: str = Field("https://us-south.ml.cloud.ibm.com", env="IBM_WATSONX_URL")
    ibm_granite_model_id: str = Field("ibm/granite-13b-chat-v2", env="IBM_GRANITE_MODEL_ID")

    # ── IBM Cloud Object Storage ────────────────────────────────
    ibm_cos_api_key: str = Field("", env="IBM_COS_API_KEY")
    ibm_cos_instance_crn: str = Field("", env="IBM_COS_INSTANCE_CRN")
    ibm_cos_endpoint: str = Field("https://s3.us-south.cloud-object-storage.appdomain.cloud", env="IBM_COS_ENDPOINT")
    ibm_cos_bucket_name: str = Field("grant-finder-data", env="IBM_COS_BUCKET_NAME")

    # ── IBM Watson Discovery ────────────────────────────────────
    ibm_discovery_api_key: str = Field("", env="IBM_DISCOVERY_API_KEY")
    ibm_discovery_url: str = Field("", env="IBM_DISCOVERY_URL")
    ibm_discovery_project_id: str = Field("", env="IBM_DISCOVERY_PROJECT_ID")

    # ── App ─────────────────────────────────────────────────────
    app_env: str = Field("development", env="APP_ENV")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    secret_key: str = Field("changeme", env="SECRET_KEY")
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # ── Database ────────────────────────────────────────────────
    database_url: str = Field("sqlite:///./grant_finder.db", env="DATABASE_URL")

    # ── Redis ───────────────────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # ── External Sources ────────────────────────────────────────
    grants_gov_api_key: str = Field("", env="GRANTS_GOV_API_KEY")
    startup_india_api_key: str = Field("", env="STARTUP_INDIA_API_KEY")
    aicte_portal_base_url: str = Field("https://www.aicte-india.org", env="AICTE_PORTAL_BASE_URL")
    dst_portal_base_url: str = Field("https://dst.gov.in", env="DST_PORTAL_BASE_URL")

    # ── Scraper ─────────────────────────────────────────────────
    scraper_user_agent: str = Field("GrantFinderBot/1.0", env="SCRAPER_USER_AGENT")
    scraper_request_delay_seconds: int = Field(2, env="SCRAPER_REQUEST_DELAY_SECONDS")
    scraper_max_retries: int = Field(3, env="SCRAPER_MAX_RETRIES")

    # ── CORS ────────────────────────────────────────────────────
    allowed_origins: str = Field("http://localhost:3000", env="ALLOWED_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
