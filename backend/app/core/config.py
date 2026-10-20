from ipaddress import ip_network

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración leída de variables de entorno y del archivo .env."""

    APP_NAME: str = "You Found Me API"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = False

    DATABASE_URL: str

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    # Uvicorn acepta encabezados reenviados solo desde estas direcciones.
    # Configura las IP o redes CIDR exactas de los proxies del despliegue.
    FORWARDED_ALLOW_IPS: str = "127.0.0.1,::1"

    API_PREFIX: str = "/api/v1"

    PROJECT_DESCRIPTION: str = "API modular para productos y avisos comerciales."

    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    # Las claves administrativas de Supabase solo se usan en el servidor.
    # Se conserva service_role para proyectos que migran a la clave secret.
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: SecretStr = SecretStr("")
    SUPABASE_AUTH_REDIRECT_URL: str = ""
    # Clave privada compartida para solicitar invitaciones de publicadores.
    # No debe incluirse entre las variables de compilación del frontend.
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
        # Un comodín permitiría falsificar X-Forwarded-For y evadir el límite de PIN.
        networks = [network.strip() for network in value.split(",") if network.strip()]
        if "*" in networks:
            raise ValueError("FORWARDED_ALLOW_IPS no puede contener '*'.")
        try:
            for network in networks:
                ip_network(network, strict=False)
        except ValueError as error:
            raise ValueError(
                "FORWARDED_ALLOW_IPS solo admite direcciones IP o redes CIDR."
            ) from error
        return ",".join(networks)

    @property
    def supabase_admin_key(self) -> str:
        """Clave administrativa vigente: prioriza la secret nueva sobre service_role."""
        return (
            self.SUPABASE_SECRET_KEY.get_secret_value()
            or self.SUPABASE_SERVICE_ROLE_KEY.get_secret_value()
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


# Instancia única importada por el resto de la aplicación.
settings = Settings()
