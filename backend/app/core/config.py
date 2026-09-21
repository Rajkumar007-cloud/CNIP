from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Neo4j
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "secretpassword"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # NLP
    SPACY_MODEL: str = "en_core_web_lg"
    TRANSFORMERS_MODEL: str = "bert-base-uncased"

    # ML
    ANOMALY_CONTAMINATION: float = 0.05
    RISK_SCORE_WEIGHTS: dict = {"pagerank": 0.4, "betweenness": 0.2, "anomaly": 0.4}

    # Redis/Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()