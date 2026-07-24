from sqlalchemy import create_engine
from .config import ADMIN_DATABASE_URL, DATABASE_URL

# Full read/write engine used by ingestion + experiment routes.
engine = create_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"),
    pool_size=10,
    pool_pre_ping=True,
)

# Admin engine for demo reset (experiments CRUD requires elevated grants).
admin_engine = create_engine(
    ADMIN_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"),
    pool_size=5,
    pool_pre_ping=True,
)
