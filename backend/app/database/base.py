from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base declarativa; sus metadatos alimentan las migraciones de Alembic."""
