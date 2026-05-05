import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base, PlatformConfig

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/data/join_cur8.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DEFAULT_CONFIG = {
    "referrer_beneficiary_weight": "500",   # 500 = 5%
    "delegation_bonus_percent": "10",       # 10% of estimated reward
    "cron_schedule": "weekly",              # weekly | monthly
    "account_creator": "cur8",
    "default_beneficiary_pct": "5.0",       # 5% default for referrers
}


def init_db():
    Base.metadata.create_all(bind=engine)
    # Add new columns to existing DBs (SQLite safe migration)
    with engine.connect() as conn:
        for col, typedef in [
            ("email_otp", "VARCHAR"),
            ("email_otp_expires", "DATETIME"),
            ("delegation_sp", "REAL"),
            ("delegation_updated_at", "DATETIME"),
            ("delegation_chain_time", "DATETIME"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE join_users ADD COLUMN {col} {typedef}"))
                conn.commit()
            except Exception:
                pass  # column already exists
    db = SessionLocal()
    try:
        for key, value in DEFAULT_CONFIG.items():
            existing = db.query(PlatformConfig).filter_by(key=key).first()
            if not existing:
                db.add(PlatformConfig(key=key, value=value))
            elif key == "default_beneficiary_pct" and existing.value == "10.0":
                # Migrate old default (10%) to new default (5%)
                existing.value = value
        db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_config(db, key: str, default: str = "") -> str:
    row = db.query(PlatformConfig).filter_by(key=key).first()
    return row.value if row else default


def set_config(db, key: str, value: str):
    row = db.query(PlatformConfig).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.add(PlatformConfig(key=key, value=value))
    db.commit()
