"""Crea la tabla de avisos.

Identificador de revisión: fd79dfed99db
Revisión anterior:
Fecha de creación: 2026-07-24 03:56:47.945016

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# Identificadores de revisión utilizados por Alembic.
revision: str = "fd79dfed99db"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Actualiza el esquema."""
    # ### comandos generados por Alembic; revísalos antes de aplicarlos ###
    op.create_table(
        "announcements",
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "type", sa.Enum("LOST", "FOUND", name="announcement_type"), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "RESOLVED",
                "CLOSED",
                name="announcement_status",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("contact_name", sa.String(length=100), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### fin de los comandos de Alembic ###


def downgrade() -> None:
    """Revierte el esquema."""
    # ### comandos generados por Alembic; revísalos antes de aplicarlos ###
    op.drop_table("announcements")
    # ### fin de los comandos de Alembic ###
