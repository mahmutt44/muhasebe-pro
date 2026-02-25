import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys

# Proje kök dizinini ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import db
from config import get_database_url

# this is the Alembic Config object
config = context.config

# SQLAlchemy URL'ini ayarla
database_url = get_database_url()
config.set_main_option('sqlalchemy.url', database_url)

# Logging ayarları
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger('alembic.env')

# MetaData objesi
target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Offline migration çalıştır."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online migration çalıştır."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
