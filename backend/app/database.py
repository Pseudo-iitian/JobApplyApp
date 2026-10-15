import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
engine = None

if db_url.startswith("postgresql"):
    try:
        # High-performance connection pool configuration for AWS RDS
        test_engine = create_engine(
            db_url,
            pool_size=20,
            max_overflow=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            pool_timeout=30,
            connect_args={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }
        )
        with test_engine.connect() as conn:
            logger.info("Successfully connected to AWS RDS PostgreSQL with connection pooling.")
        engine = test_engine
    except Exception as e:
        logger.warning(
            f"Could not connect to AWS RDS PostgreSQL ({e}). "
            "Falling back to local SQLite (jobapply.db). "
            "Please verify AWS credentials in backend/.env."
        )
        engine = create_engine(
            "sqlite:///./jobapply.db",
            connect_args={"check_same_thread": False}
        )
else:
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
