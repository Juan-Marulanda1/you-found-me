"""Exige consentimiento explícito para mostrar el teléfono de una publicación.

Identificador de revisión: 20261019_public_phone
Revisión anterior: 20261019_marketplace
Fecha de creación: 2026-10-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261019_public_phone"
down_revision: str | Sequence[str] | None = "20261019_marketplace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in ("announcements", "products"):
        op.add_column(
            table_name,
            sa.Column(
                "contact_phone_public",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    for table_name in ("products", "announcements"):
        op.drop_column(table_name, "contact_phone_public")
