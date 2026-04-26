import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

ENV_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

load_dotenv(ENV_FILE_PATH)

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def get_cr_api_token():
    env_values = dotenv_values(ENV_FILE_PATH)
    token = env_values.get("CR_API_TOKEN") or os.getenv("CR_API_TOKEN")

    if token:
        return token.strip()

    return None


