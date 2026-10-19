from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdminPinCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    admin_pin: str = Field(min_length=6, max_length=12, pattern=r"^\d{6,12}$")


class AdminPinAuthSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Four-digit values remain accepted so records created by the first API
    # version can still be managed after their hashes are migrated.
    admin_pin: str = Field(min_length=4, max_length=12, pattern=r"^\d{4,12}$")


class PublicationUpdateSchema(AdminPinAuthSchema):
    nullable_fields: ClassVar[set[str]] = set()

    new_admin_pin: str | None = Field(
        default=None, min_length=6, max_length=12, pattern=r"^\d{6,12}$"
    )

    @model_validator(mode="after")
    def validate_update_fields(self):
        changed_fields = self.model_fields_set - {"admin_pin"}
        if not changed_fields:
            raise ValueError("At least one publication field must be provided.")

        for field in changed_fields - self.nullable_fields:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")

        return self
