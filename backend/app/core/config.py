# backend/app/core/config.py
import os
from dotenv import load_dotenv, find_dotenv
from functools import lru_cache

# Load .env file (local only)
load_dotenv(find_dotenv())

@lru_cache
def get_settings():
    IS_DOCKER = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "1"

    API_KEY = os.getenv("API_KEY")
    DATASET_URL = os.getenv("DATASET_URL")

    if IS_DOCKER:
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/soochna_db")
        REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    else:
        DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/soochna_db")
        REDIS_URL = os.getenv("LOCAL_REDIS_URL", "redis://localhost:6379/0")

    return type(
        "Settings",
        (),
        {
            "API_KEY": API_KEY,
            "DATASET_URL": DATASET_URL,
            "DATABASE_URL": DATABASE_URL,
            "REDIS_URL": REDIS_URL,
            "IS_DOCKER": IS_DOCKER,
        },
    )()

settings = get_settings()
