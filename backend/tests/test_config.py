"""Application settings tests."""

from app.core.config import Settings


def test_new_settings_have_startup_safe_defaults():
    settings = Settings(_env_file=None)

    assert settings.app_name == "Vision Pass"
    assert settings.face_model_name == "buffalo_l"
    assert settings.face_detection_confidence == 0.60
    assert settings.face_recognition_threshold == 0.45
    assert settings.face_enrollment_min_quality == 0.70
    assert settings.face_duplicate_threshold == 0.40
    assert settings.access_confidence_threshold == 0.65
    assert settings.access_unknown_face_action == "manual_review"
    assert settings.access_outside_shift_action == "manual_review"
    assert settings.access_holiday_action == "manual_review"
    assert settings.access_shift_grace_minutes == 0
    assert settings.attendance_duplicate_cooldown_minutes == 10
    assert settings.attendance_late_grace_minutes == 10
    assert settings.attendance_auto_checkout_hours == 12
    assert settings.camera_frame_interval_seconds == 3
    assert settings.camera_request_timeout_seconds == 10
    assert settings.storage_backend == "local"
    assert settings.upload_max_image_mb == 5


def test_new_settings_parse_typed_environment_values(monkeypatch):
    monkeypatch.setenv("FACE_RECOGNITION_THRESHOLD", "0.52")
    monkeypatch.setenv("ATTENDANCE_DUPLICATE_COOLDOWN_MINUTES", "15")
    monkeypatch.setenv("CAMERA_FRAME_INTERVAL_SECONDS", "4")
    monkeypatch.setenv("UPLOAD_MAX_IMAGE_MB", "8")
    monkeypatch.setenv("ACCESS_CONFIDENCE_THRESHOLD", "0.72")
    monkeypatch.setenv("ACCESS_OUTSIDE_SHIFT_ACTION", "denied")

    settings = Settings(_env_file=None)

    assert settings.face_recognition_threshold == 0.52
    assert settings.attendance_duplicate_cooldown_minutes == 15
    assert settings.camera_frame_interval_seconds == 4
    assert settings.upload_max_image_mb == 8
    assert settings.access_confidence_threshold == 0.72
    assert settings.access_outside_shift_action == "denied"
