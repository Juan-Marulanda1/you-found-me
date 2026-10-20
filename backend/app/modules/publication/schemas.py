from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdminPinCreateSchema(BaseModel):
    """Base de creación: rechaza campos desconocidos y valida PIN nuevos."""

    model_config = ConfigDict(extra="forbid")

    admin_pin: str | None = Field(
        default=None, min_length=6, max_length=12, pattern=r"^\d{6,12}$"
    )


class PublicationCreateSchema(AdminPinCreateSchema):
    """Campos comunes al crear cualquier tipo de publicación."""

    # El teléfono es privado salvo que quien publica autorice mostrarlo.
    contact_phone_public: bool = False


class AdminPinAuthSchema(BaseModel):
    """Cuerpo de gestión; el PIN solo aplica a registros antiguos."""

    model_config = ConfigDict(extra="forbid")

    # Acepta PIN de cuatro dígitos para administrar registros de la primera versión.
    admin_pin: str | None = Field(
        default=None, min_length=4, max_length=12, pattern=r"^\d{4,12}$"
    )


class PublicationUpdateSchema(AdminPinAuthSchema):
    """Actualización parcial: exige un campo y solo admite null en nullable_fields."""

    nullable_fields: ClassVar[set[str]] = set()

    new_admin_pin: str | None = Field(
        default=None, min_length=6, max_length=12, pattern=r"^\d{6,12}$"
    )

    @model_validator(mode="after")
    def validate_update_fields(self):
        changed_fields = self.model_fields_set - {"admin_pin"}
        if not changed_fields:
            raise ValueError("Envía al menos un campo para actualizar.")

        for field in changed_fields - self.nullable_fields:
            if getattr(self, field) is None:
                raise ValueError(f"El campo «{field}» no puede quedar vacío.")

        return self
