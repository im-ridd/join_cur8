from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class JoinUser(Base):
    __tablename__ = "join_users"

    id = Column(String, primary_key=True)
    steem_username = Column(String, unique=True, nullable=True)
    auth_provider = Column(String, nullable=False)
    auth_id = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    referrer_steem = Column(String, nullable=True)
    account_created = Column(Boolean, default=False)
    email_otp = Column(String, nullable=True)
    email_otp_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    # Cached delegation info — refreshed manually from admin panel
    delegation_sp = Column(Float, nullable=True)
    delegation_updated_at = Column(DateTime, nullable=True)   # when we last scanned
    delegation_chain_time = Column(DateTime, nullable=True)   # when user last set/updated delegation on chain

    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_id", name="uq_auth"),
    )


class ReferrerConfig(Base):
    """Per-referrer beneficiary percentage used by games.cur8.fun when publishing."""
    __tablename__ = "referrer_configs"

    steem_username = Column(String, primary_key=True)
    beneficiary_pct = Column(Float, default=10.0)  # e.g. 10.0 = 10%
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PlatformConfig(Base):
    __tablename__ = "platform_config"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
