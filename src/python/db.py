"""
Database connections: MySQL (SQLAlchemy) + Redis.

Usage:
    from db import SessionLocal, redis_client
    with SessionLocal() as session:
        ...
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis

from config.settings import settings

engine = create_engine(
    settings.DB_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)
