from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Operational Anomaly Radar"
    env: str = "dev"

    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/anomaly_radar",
        alias="DATABASE_URL",
    )

    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="radar", alias="ADMIN_PASSWORD")

    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")

    anomaly_threshold: float = 0.85
    model_min_samples: int = 50
    isolation_forest_contamination: float = 0.05
    model_window_size: int = 200

    model_strategy: str = Field(default="hybrid", alias="MODEL_STRATEGY")
    autoencoder_enabled: bool = Field(default=False, alias="AUTOENCODER_ENABLED")
    autoencoder_window_size: int = Field(default=30, alias="AUTOENCODER_WINDOW_SIZE")
    autoencoder_latent_dim: int = Field(default=8, alias="AUTOENCODER_LATENT_DIM")
    autoencoder_threshold_quantile: float = Field(default=0.95, alias="AUTOENCODER_THRESHOLD_Q")
    autoencoder_min_train_samples: int = Field(default=200, alias="AUTOENCODER_MIN_SAMPLES")
    autoencoder_retrain_interval: int = Field(default=200, alias="AUTOENCODER_RETRAIN_INTERVAL")
    autoencoder_epochs: int = Field(default=20, alias="AUTOENCODER_EPOCHS")
    autoencoder_batch_size: int = Field(default=32, alias="AUTOENCODER_BATCH_SIZE")

    kafka_enabled: bool = Field(default=False, alias="KAFKA_ENABLED")
    kafka_bootstrap_servers: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic: str = Field(default="operational_metrics", alias="KAFKA_TOPIC")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=("settings_",),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
