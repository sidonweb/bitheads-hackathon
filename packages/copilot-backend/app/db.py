from sqlalchemy import create_engine
from .config import DATABASE_URL

# Full read/write engine used by ingestion + experiment routes.
# psycopg3 driver.
engine = create_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"),
    pool_size=10,
    pool_pre_ping=True,
)
