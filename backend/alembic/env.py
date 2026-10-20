from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import app.database.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.database.base import Base

# -----------------------------------------------------------------------------
# Alembic Configuration
# -----------------------------------------------------------------------------

config = context.config

# Usar la configuración centralizada de la aplicación
database_url = settings.DATABASE_URL.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url)

# Configuración de logs
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------------------------------------------------------
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecuta las migraciones en modo offline."""

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta las migraciones en modo online."""

    def run_with_connection(connection) -> None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        run_with_connection(supplied_connection)
        return

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        run_with_connection(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
