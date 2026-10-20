from ipaddress import ip_network

from pydantic import Field, SecretStr, field_validator
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

    # Keep Supabase admin keys on the server only. The legacy service_role key
    # remains supported while projects migrate to the newer secret key.
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: SecretStr = SecretStr("")
    SUPABASE_AUTH_REDIRECT_URL: str = ""
    # Shared server-side key required to request a publisher account invitation.
    # Keep it out of frontend build-time variables.
    PUBLICATION_CREATION_KEY: SecretStr = SecretStr("")
    SUPABASE_SECRET_KEY: SecretStr = SecretStr("")
    SUPABASE_SERVICE_ROLE_KEY: SecretStr = SecretStr("")
    SUPABASE_PRODUCT_IMAGES_BUCKET: str = "product-images"
    PRODUCT_IMAGE_MAX_BYTES: int = Field(default=5 * 1024 * 1024, gt=0)
    PRODUCT_IMAGE_MAX_COUNT: int = Field(default=8, gt=0, le=50)
    ANNOUNCEMENT_IMAGE_MAX_COUNT: int = Field(default=1, gt=0, le=50)

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

    @property
    def supabase_storage_admin_key(self) -> str:
        return (
            self.SUPABASE_SECRET_KEY.get_secret_value()
            or self.SUPABASE_SERVICE_ROLE_KEY.get_secret_value()
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
