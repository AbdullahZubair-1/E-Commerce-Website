from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

# pydantic-settings (below) only loads .env into its OWN Settings object --
# it does NOT populate os.environ. Several integrations (Cal.com, Composio,
# Make.com) read their own env vars directly via os.getenv() in their own
# modules, which only ever see real OS environment variables, not anything
# that exists only in .env. This call is what actually makes .env values
# visible to plain os.getenv() calls anywhere else in the app -- without it,
# those integrations silently behave as "not configured" even when the
# key is right there in .env.
load_dotenv()
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://chemisto:chemisto_pass@localhost:5432/chemisto_db"

    # JWT
    SECRET_KEY: str = "change-this-secret-key-in-production-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Owner credentials -- used to auto-create the initial admin account for
    # each site on backend startup (only if that site has no owner yet).
    OWNER_EMAIL: str = "owner@chemisto.com"
    OWNER_PASSWORD: str = "ChemistoOwner2024!"
    OWNER_FIRST_NAME: str = "Store"
    OWNER_LAST_NAME: str = "Owner"

    CHEMISTO_FOOD_OWNER_EMAIL: str = "owner@chemistofood.com"
    CHEMISTO_FOOD_OWNER_PASSWORD: str = "ChemistoFoodOwner2024!"
    CHEMISTO_FOOD_OWNER_FIRST_NAME: str = "Food"
    CHEMISTO_FOOD_OWNER_LAST_NAME: str = "Owner"

    # Organization-level superadmin -- oversees every site, auto-created on
    # startup just like the per-site owners.
    SUPERADMIN_EMAIL: str = "superadmin@chemisto.org"
    SUPERADMIN_PASSWORD: str = "SuperAdmin2024!"
    SUPERADMIN_FIRST_NAME: str = "Org"
    SUPERADMIN_LAST_NAME: str = "Admin"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 5242880  # 5MB

    # Chatbot API keys
    GOOGLE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GOOGLE_PROJECT_ID: str | None = None
    GOOGLE_LOCATION: str = "us-central1"

    # App
    APP_NAME: str = "CHEMISTO's Store"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # DB Pool
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Several integrations (Cal.com, Composio, Make.com) read their own
        # env vars directly via os.getenv() in their own modules, rather
        # than being declared as fields here. Without this, pydantic-settings
        # crashes the whole app on startup the moment any of those vars
        # exist in .env, since it forbids "unknown" keys by default.
        extra = "ignore"


settings = Settings()