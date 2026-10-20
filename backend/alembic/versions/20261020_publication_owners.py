"""Agrega propiedad de cuenta reutilizable a las publicaciones.

Identificador de revisión: 20261020_publication_owners
Revisión anterior: 20261020_announcement_images
Fecha de creación: 2026-10-20

Los registros existentes quedan sin reclamar (owner_id es NULL). Se conservan
los hashes de PIN para que sus propietarios puedan reclamarlos al iniciar sesión.

Al revertir, los registros administrados por cuenta y sin PIN reciben un valor
inutilizable antes de restaurar la restricción NOT NULL. La reversión no puede
restaurar la gestión por PIN de registros creados después de activar las cuentas.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261020_publication_owners"
down_revision: str | Sequence[str] | None = "20261020_announcement_images"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "publication_invitations",
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column(
            "invited_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("email", name="pk_publication_invitations"),
    )
    op.create_table(
        "publication_owners",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_publication_owners"),
    )

    for table_name in ("products", "announcements"):
        op.alter_column(table_name, "admin_pin_hash", nullable=True)
        op.add_column(table_name, sa.Column("owner_id", sa.UUID(), nullable=True))
        op.create_index(
            f"ix_{table_name}_owner_id", table_name, ["owner_id"], unique=False
        )
        op.create_foreign_key(
            f"fk_{table_name}_owner_id_publication_owners",
            table_name,
            "publication_owners",
            ["owner_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    for table_name in ("announcements", "products"):
        op.drop_constraint(
            f"fk_{table_name}_owner_id_publication_owners",
            table_name,
            type_="foreignkey",
        )
        op.drop_index(f"ix_{table_name}_owner_id", table_name=table_name)
        op.drop_column(table_name, "owner_id")
        op.execute(
            sa.text(
                f"UPDATE {table_name} "
                "SET admin_pin_hash = 'account-managed-no-pin' "
                "WHERE admin_pin_hash IS NULL"
            )
        )
        op.alter_column(table_name, "admin_pin_hash", nullable=False)
    op.drop_table("publication_owners")
    op.drop_table("publication_invitations")
