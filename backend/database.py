"""
Smart Fence - Database Setup (SQLAlchemy + SQLite)
Provides session management, engine configuration, and table initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from ai.config import DATABASE_URL

# Connect args needed for SQLite concurrency
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all database tables and seeds default zones if missing."""
    import json
    from backend.models import ZoneRecord, SystemLog
    from ai.config import DEFAULT_ZONES

    Base.metadata.create_all(bind=engine)

    # Seed default zones if empty
    db = SessionLocal()
    try:
        existing_zones = db.query(ZoneRecord).count()
        if existing_zones == 0:
            for name, coords in DEFAULT_ZONES.items():
                zone = ZoneRecord(
                    name=f"{name} Perimeter",
                    zone_type=name,
                    coordinates=json.dumps(coords),
                    enabled=True
                )
                db.add(zone)
            
            # Add initial system log
            log = SystemLog(
                component="DATABASE",
                status="CONNECTED",
                message="SQLite database initialized with default zones."
            )
            db.add(log)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()
