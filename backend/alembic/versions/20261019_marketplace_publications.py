"""Add business announcements and product listings.

Revision ID: 20261019_marketplace
Revises: 1b159c348e7e
Create Date: 2026-10-19

"""

import hashlib
import secrets
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261019_marketplace"
down_revision: str | Sequence[str] | None = "1b159c348e7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PIN_HASH_ITERATIONS = 310_000


def _hash_legacy_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), salt, PIN_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${PIN_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("announcements", sa.Column("admin_pin_hash", sa.String(length=128)))
    legacy_rows = bind.execute(sa.text("SELECT id, admin_pin FROM announcements")).all()
    for announcement_id, admin_pin in legacy_rows:
        bind.execute(
            sa.text(
                "UPDATE announcements SET admin_pin_hash = :pin_hash WHERE id = :id"
            ),
            {"pin_hash": _hash_legacy_pin(admin_pin), "id": announcement_id},
        )
    op.alter_column("announcements", "admin_pin_hash", nullable=False)
    op.drop_column("announcements", "admin_pin")

    op.add_column(
        "announcements", sa.Column("category", sa.String(length=80), nullable=True)
    )
    op.add_column("announcements", sa.Column("business_name", sa.String(length=150)))
    op.add_column("announcements", sa.Column("website_url", sa.String(length=2048)))
    op.add_column("announcements", sa.Column("contact_email", sa.String(length=254)))
    op.execute(
        "UPDATE announcements SET category = LOWER(type::text) WHERE category IS NULL"
    )
    op.alter_column("announcements", "category", nullable=False)
    op.drop_column("announcements", "type")
    op.execute("DROP TYPE announcement_type")
    op.alter_column(
        "announcements",
        "status",
        type_=sa.String(length=20),
        postgresql_using=(
            "CASE status::text WHEN 'OPEN' THEN 'ACTIVE' "
            "WHEN 'RESOLVED' THEN 'CLOSED' ELSE 'CLOSED' END"
        ),
    )
    op.execute("DROP TYPE announcement_status")
    op.create_check_constraint(
        "ck_announcements_status",
        "announcements",
        "status IN ('ACTIVE', 'PAUSED', 'CLOSED')",
    )

    op.create_index("ix_announcements_city", "announcements", ["city"])
    op.create_index("ix_announcements_category", "announcements", ["category"])
    op.create_index("ix_announcements_status", "announcements", ["status"])

    op.create_table(
        "products",
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), server_default="COP", nullable=False
        ),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column("contact_name", sa.String(length=100), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=False),
        sa.Column("contact_email", sa.String(length=254), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("admin_pin_hash", sa.String(length=128), nullable=False),
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
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SOLD', 'CLOSED')", name="ck_products_status"
        ),
        sa.CheckConstraint("price > 0", name="ck_products_price_positive"),
        sa.CheckConstraint(
            "quantity IS NULL OR quantity >= 0",
            name="ck_products_quantity_nonnegative",
        ),
    )
    op.create_index("ix_products_city", "products", ["city"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_status", "products", ["status"])


def downgrade() -> None:
    raise RuntimeError(
        "This migration hashes existing management PINs, so it cannot safely "
        "restore the previous plaintext schema. Restore a database backup instead."
    )
