from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.database.base import Base

# -----------------------------------------------------------------------------
# Alembic Configuration
# -----------------------------------------------------------------------------

config = context.config

# Usar la configuración centralizada de la aplicación
config.set_main_option("sqlalchemy.url", str(settings.database_url))

# Configuración de logs
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------------------------------------------------------
# Importar modelos aquí
#
# Cuando creemos el primer modelo (Announcement) simplemente agregaremos:
#
# from app.modules.announcement.model import Announcement
#
# El import es suficiente para que SQLAlchemy registre automáticamente
# la tabla dentro de Base.metadata.
# -----------------------------------------------------------------------------

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecuta las migraciones en modo offline."""

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta las migraciones en modo online."""

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
