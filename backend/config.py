# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME = "ThreatVerse Local"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    NEO4J_URI = os.getenv("NEO4J_URI", "")  # e.g., bolt://localhost:7687
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "admin")
    DEFAULT_ADMIN_PASS = os.getenv("ADMIN_PASS", "ChangeMe123")

settings = Settings()
