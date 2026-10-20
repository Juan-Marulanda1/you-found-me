import os
import unittest
from uuid import uuid4

from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from alembic import command
from app.core.security import verify_admin_pin

MIGRATION_TEST_DATABASE_URL = os.getenv("MIGRATION_TEST_DATABASE_URL")


@unittest.skipUnless(
    MIGRATION_TEST_DATABASE_URL,
    "Set MIGRATION_TEST_DATABASE_URL to a disposable local PostgreSQL database.",
)
class MarketplaceMigrationTests(unittest.TestCase):
    def test_legacy_records_survive_migration_and_pin_is_hashed(self):
        url = make_url(MIGRATION_TEST_DATABASE_URL)
        if url.get_backend_name() != "postgresql":
            self.fail("Migration test requires PostgreSQL.")
        if url.host not in {"localhost", "127.0.0.1", "::1"}:
            self.fail("Migration test only runs against a local PostgreSQL host.")
        if "test" not in (url.database or "").lower():
            self.fail("Migration test database name must contain 'test'.")

        original_database_url = os.environ.get("DATABASE_URL")
        original_debug = os.environ.get("DEBUG")
        os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
        os.environ["DEBUG"] = "false"
        engine = None
        schema_name = f"yfm_migration_test_{uuid4().hex}"
        try:
            engine = create_engine(url)
            with engine.connect() as connection:
                connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
                connection.commit()
                connection.execute(text(f'SET search_path TO "{schema_name}"'))
                connection.commit()

                config = Config("alembic.ini")
                config.attributes["connection"] = connection
                command.upgrade(config, "1b159c348e7e")

                connection.execute(
                    text(
                        """
                        INSERT INTO announcements (
                            title, description, type, status, contact_name,
                            contact_phone, city, admin_pin
                        ) VALUES
                            ('Aviso abierto', 'Descripción de prueba', 'FOUND', 'OPEN',
                             'Ana', '3001234567', 'Medellín', '4821'),
                            ('Aviso resuelto', 'Descripción de prueba',
                             'LOST', 'RESOLVED',
                             'Luis', '3007654321', 'Bogotá', '9357')
                        """
                    )
                )
                connection.commit()

                command.upgrade(config, "head")
                rows = (
                    connection.execute(
                        text(
                            """
                        SELECT category, status, admin_pin_hash, contact_phone_public
                        FROM announcements ORDER BY title
                        """
                        )
                    )
                    .mappings()
                    .all()
                )

                self.assertEqual([row["category"] for row in rows], ["found", "lost"])
                self.assertEqual([row["status"] for row in rows], ["ACTIVE", "CLOSED"])
                self.assertTrue(verify_admin_pin("4821", rows[0]["admin_pin_hash"]))
                self.assertTrue(verify_admin_pin("9357", rows[1]["admin_pin_hash"]))
                self.assertTrue(
                    all(row["contact_phone_public"] is False for row in rows)
                )
                self.assertEqual(
                    connection.execute(
                        text("SELECT to_regclass('products')")
                    ).scalar_one(),
                    "products",
                )
        finally:
            try:
                if engine is not None:
                    try:
                        with engine.begin() as connection:
                            connection.execute(text("SET search_path TO public"))
                            connection.execute(
                                text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                            )
                    finally:
                        engine.dispose()
            finally:
                if original_database_url is None:
                    os.environ.pop("DATABASE_URL", None)
                else:
                    os.environ["DATABASE_URL"] = original_database_url
                if original_debug is None:
                    os.environ.pop("DEBUG", None)
                else:
                    os.environ["DEBUG"] = original_debug


if __name__ == "__main__":
    unittest.main()
