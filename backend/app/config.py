import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://admin:password@localhost:5432/ausclean"
    
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Xero
    XERO_CLIENT_ID: str = os.getenv("XERO_CLIENT_ID", "")
    XERO_CLIENT_SECRET: str = os.getenv("XERO_CLIENT_SECRET", "")
    XERO_TENANT_ID: str = os.getenv("XERO_TENANT_ID", "")
    XERO_ACCESS_TOKEN: str = os.getenv("XERO_ACCESS_TOKEN", "")
    
    # NDIS PRODA
    PRODA_PRIVATE_KEY_PEM: str = os.getenv("PRODA_PRIVATE_KEY_PEM", "")
    PRODA_SOFTWARE_INSTANCE_ID: str = os.getenv("PRODA_SOFTWARE_INSTANCE_ID", "")
    
    # OpenAI / LangChain
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "ausclean-pro")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Inngest
    INNGEST_EVENT_KEY: str = os.getenv("INNGEST_EVENT_KEY", "")
    INNGEST_SIGNING_KEY: str = os.getenv("INNGEST_SIGNING_KEY", "")
    
    # Grafana
    GRAFANA_URL: str = os.getenv("GRAFANA_URL", "http://localhost:3000")
    GRAFANA_API_KEY: str = os.getenv("GRAFANA_API_KEY", "")
    
    # App
    APP_NAME: str = "AusClean Pro"
    APP_VERSION: str = "5.0.0"
    DEBUG: bool = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
