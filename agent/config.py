from __future__ import annotations


import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add Render's PostgreSQL External Database URL"
        )

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url



def get_groq_api_key() -> str:
    groq_api_key = os.getenv("GROQ_API_KEY2")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY2 is missing. Please add it to your .env file.")
    return groq_api_key



DATABASE_URL = get_database_url()
GROQ_API_KEY2 = get_groq_api_key()

    
