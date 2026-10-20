"""Agrega el PIN de administración a los avisos.

Identificador de revisión: 1b159c348e7e
Revisión anterior: fd79dfed99db
Fecha de creación: 2026-07-28 03:33:30.943303

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Identificadores de revisión utilizados por Alembic.
revision: str = "1b159c348e7e"
down_revision: str | Sequence[str] | None = "fd79dfed99db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Actualiza el esquema."""
    # ### comandos generados por Alembic; revísalos antes de aplicarlos ###
    op.add_column(
        "announcements", sa.Column("admin_pin", sa.String(length=4), nullable=False)
    )
    # ### fin de los comandos de Alembic ###


def downgrade() -> None:
    """Revierte el esquema."""
    # ### comandos generados por Alembic; revísalos antes de aplicarlos ###
    op.drop_column("announcements", "admin_pin")
    # ### fin de los comandos de Alembic ###
