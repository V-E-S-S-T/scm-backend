import os
from typing import Optional
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Config:
    """Application configuration"""

    # Application settings
    app_name: str = "AI Supply Chain Management Platform"
    version: str = "1.0.0"
    debug: bool = False

    # Database settings
    database_url: str = "sqlite:///ai_supplychain.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    sql_echo: bool = False

    # AI model settings
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-pro"
    ai_timeout: int = 30
    ai_fallback_enabled: bool = True

    # API settings
    cors_origins: list = None
    api_rate_limit: str = "100 per hour"
    max_content_length: int = 16 * 1024 * 1024  # 16MB

    # Cache settings
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600

    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Business settings
    default_forecast_period: int = 6
    max_forecast_months: int = 12
    min_confidence_score: float = 0.6
    default_currency: str = "INR"
    default_timezone: str = "Asia/Kolkata"

    # Festival and seasonal settings
    festival_data_source: str = "internal"
    update_festival_data: bool = True

    # Security settings
    secret_key: str = "ai-supplychain-secret-key"
    jwt_secret_key: str = "jwt-secret-key"
    jwt_expiration_hours: int = 24

    # File upload settings
    upload_folder: str = "uploads"
    allowed_extensions: list = None

    def __post_init__(self):
        """Initialize default values that need processing"""

        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

        if self.allowed_extensions is None:
            self.allowed_extensions = ["csv", "xlsx", "xls", "json"]


class DevelopmentConfig(Config):
    """Development environment configuration"""

    debug: bool = True
    sql_echo: bool = True
    log_level: str = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration"""

    debug: bool = False
    sql_echo: bool = False
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost/ai_supplychain"
    )

    def __post_init__(self):
        super().__post_init__()
        # Override with environment variables in production
        self.secret_key = os.getenv("SECRET_KEY", "secure-production-secret")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "secure-jwt-secret")


class TestingConfig(Config):
    """Testing environment configuration"""

    debug: bool = True
    database_url: str = "sqlite:///:memory:"
    ai_fallback_enabled: bool = True

    def __post_init__(self):
        super().__post_init__()
        # Use fallback models for testing
        self.gemini_api_key = None


@lru_cache()
def get_config() -> Config:
    """Get configuration based on environment"""

    env = os.getenv("FLASK_ENV", os.getenv("FASTAPI_ENV", "development")).lower()

    # Load environment variables
    config_dict = {
        # Application
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        # Database
        "database_url": os.getenv("DATABASE_URL", "sqlite:///ai_supplychain.db"),
        "db_pool_size": int(os.getenv("DB_POOL_SIZE", 10)),
        "db_max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 20)),
        "sql_echo": os.getenv("SQL_ECHO", "false").lower() == "true",
        # AI
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
        "ai_timeout": int(os.getenv("AI_TIMEOUT", 30)),
        "ai_fallback_enabled": os.getenv("AI_FALLBACK_ENABLED", "true").lower()
        == "true",
        # API
        "cors_origins": os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(","),
        "max_content_length": int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)),
        # Cache
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        "cache_ttl": int(os.getenv("CACHE_TTL", 3600)),
        # Logging
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_file": os.getenv("LOG_FILE", "logs/app.log"),
        # Business
        "default_forecast_period": int(os.getenv("DEFAULT_FORECAST_PERIOD", 6)),
        "max_forecast_months": int(os.getenv("MAX_FORECAST_MONTHS", 12)),
        "min_confidence_score": float(os.getenv("MIN_CONFIDENCE_SCORE", 0.6)),
        "default_currency": os.getenv("DEFAULT_CURRENCY", "INR"),
        "default_timezone": os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata"),
        # Security
        "secret_key": os.getenv("SECRET_KEY", "ai-supplychain-secret-key"),
        "jwt_secret_key": os.getenv("JWT_SECRET_KEY", "jwt-secret-key"),
        "jwt_expiration_hours": int(os.getenv("JWT_EXPIRATION_HOURS", 24)),
        # File upload
        "upload_folder": os.getenv("UPLOAD_FOLDER", "uploads"),
        "allowed_extensions": os.getenv(
            "ALLOWED_EXTENSIONS", "csv,xlsx,xls,json"
        ).split(","),
    }

    if env == "production":
        config = ProductionConfig(**config_dict)
    elif env == "testing":
        config = TestingConfig(**config_dict)
    else:
        config = DevelopmentConfig(**config_dict)

    # Ensure required directories exist
    os.makedirs(os.path.dirname(config.log_file), exist_ok=True)
    os.makedirs(config.upload_folder, exist_ok=True)

    return config


def get_database_url() -> str:
    """Get database URL"""
    return get_config().database_url


def get_ai_config() -> dict:
    """Get AI configuration"""
    config = get_config()
    return {
        "api_key": config.gemini_api_key,
        "model": config.gemini_model,
        "timeout": config.ai_timeout,
        "fallback_enabled": config.ai_fallback_enabled,
    }


def get_cors_origins() -> list:
    """Get CORS origins"""
    return get_config().cors_origins


def is_development() -> bool:
    """Check if running in development mode"""
    return get_config().debug


def is_production() -> bool:
    """Check if running in production mode"""
    env = os.getenv("FLASK_ENV", os.getenv("FASTAPI_ENV", "development")).lower()
    return env == "production"


def get_log_config() -> dict:
    """Get logging configuration"""
    config = get_config()
    return {
        "level": config.log_level,
        "file": config.log_file,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }
