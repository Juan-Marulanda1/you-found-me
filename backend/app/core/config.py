from ipaddress import ip_network

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "You Found Me API"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = False

    DATABASE_URL: str

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    # Configure this with the exact proxy IPs/CIDRs used by the deployment.
    # Uvicorn trusts forwarded headers only from these addresses.
    FORWARDED_ALLOW_IPS: str = "127.0.0.1,::1"

    API_PREFIX: str = "/api/v1"

    PROJECT_DESCRIPTION: str = "API for product listings and business announcements."

    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    @field_validator("FORWARDED_ALLOW_IPS")
    @classmethod
    def validate_forwarded_allow_ips(cls, value: str) -> str:
        networks = [network.strip() for network in value.split(",") if network.strip()]
        if "*" in networks:
            raise ValueError("FORWARDED_ALLOW_IPS must not contain '*'.")
        try:
            for network in networks:
                ip_network(network, strict=False)
        except ValueError as error:
            raise ValueError(
                "FORWARDED_ALLOW_IPS must contain IP addresses or CIDR networks."
            ) from error
        return ",".join(networks)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
