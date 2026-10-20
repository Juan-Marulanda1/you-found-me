"""Agrega metadatos de imágenes de avisos almacenadas en Supabase.

Identificador de revisión: 20261020_announcement_images
Revisión anterior: 20261019_product_images
Fecha de creación: 2026-10-20

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261020_announcement_images"
down_revision: str | Sequence[str] | None = "20261019_product_images"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "announcement_images",
        sa.Column("announcement_id", sa.UUID(), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "size_bytes > 0", name="ck_announcement_images_size_positive"
        ),
        sa.CheckConstraint(
            "position >= 0", name="ck_announcement_images_position_nonnegative"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'READY')", name="ck_announcement_images_status"
        ),
        sa.ForeignKeyConstraint(
            ["announcement_id"], ["announcements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_path"),
    )
    op.create_index(
        "ix_announcement_images_announcement_id",
        "announcement_images",
        ["announcement_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_announcement_images_announcement_id", table_name="announcement_images"
    )
    op.drop_table("announcement_images")
