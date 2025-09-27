"""
Dependencies for API endpoints.
Includes database connections, Redis connections, and shared utilities.
"""

import redis
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.config import settings

# SQLAlchemy setup
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

# Async database connection
database = Database(settings.DATABASE_URL)

# Redis connection
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
    decode_responses=True  # Automatically decode bytes to strings
)

# Dependency functions
async def get_database() -> Database:
    """Get database connection for async operations."""
    return database

def get_redis() -> redis.Redis:
    """Get Redis client connection."""
    return redis_client

def get_db():
    """Get database session for sync operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Connection management
@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[Database, None]:
    """Context manager for database connections."""
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()

# Health check functions
async def check_database_health() -> dict:
    """Check if database is accessible."""
    try:
        await database.connect()
        query = "SELECT 1"
        await database.fetch_one(query)
        await database.disconnect()
        return {"database": "healthy"}
    except Exception as e:
        return {"database": "unhealthy", "error": str(e)}

def check_redis_health() -> dict:
    """Check if Redis is accessible."""
    try:
        redis_client.ping()
        return {"redis": "healthy"}
    except Exception as e:
        return {"redis": "unhealthy", "error": str(e)}

# Initialize connections on startup
async def startup_db():
    """Initialize database connection on startup."""
    await database.connect()
    print("Database connected")

async def shutdown_db():
    """Close database connection on shutdown."""
    await database.disconnect()
    print("Database disconnected")