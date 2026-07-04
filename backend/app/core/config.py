"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vision Pass"
    environment: str = "development"
    api_v1_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://visionpass:visionpass@localhost:5432/visionpass"
    jwt_secret: str = "change-me"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )
    frontend_url: str | None = None

    # Face recognition and enrollment defaults. Unit-interval constraints keep
    # invalid confidence/quality values from reaching recognition services.
    face_model_name: str = Field(default="buffalo_l", min_length=1)
    face_detection_confidence: float = Field(default=0.60, ge=0, le=1)
    face_recognition_threshold: float = Field(default=0.45, ge=0, le=1)
    face_enrollment_min_quality: float = Field(default=0.70, ge=0, le=1)
    face_duplicate_threshold: float = Field(default=0.40, ge=0, le=1)

    access_confidence_threshold: float = Field(default=0.65, ge=0, le=1)
    access_unknown_face_action: Literal["denied", "manual_review"] = "manual_review"
    access_outside_shift_action: Literal["denied", "manual_review"] = "manual_review"
    access_holiday_action: Literal["denied", "manual_review"] = "manual_review"
    access_shift_grace_minutes: int = Field(default=0, ge=0, le=240)

    attendance_duplicate_cooldown_minutes: int = Field(default=10, ge=1)
    attendance_late_grace_minutes: int = Field(default=10, ge=0)
    attendance_auto_checkout_hours: int = Field(default=12, ge=1)

    camera_frame_interval_seconds: int = Field(default=3, ge=1)
    camera_request_timeout_seconds: int = Field(default=10, ge=1)

    storage_backend: Literal["local"] = "local"
    upload_dir: str = "uploads"
    upload_max_image_mb: int = Field(default=5, ge=1)
    seed_demo_data: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
