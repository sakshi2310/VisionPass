"""Database-free checks for common camera access and phone webcam schemas."""

from fastapi.routing import APIRoute

from app.api.v1.endpoints import cameras
from app.schemas.camera import CameraCreate


def test_phone_ip_webcam_payload_supports_feature_scope() -> None:
    payload = CameraCreate(
        name="Lobby phone",
        location="Lobby",
        camera_type="phone_ip_webcam",
        phone_ip="192.168.1.20",
        port=8080,
        stream_url="http://192.168.1.20:8080/video",
        snapshot_url="http://192.168.1.20:8080/shot.jpg",
        assigned_feature_scope="both",
    )

    assert payload.port == 8080
    assert payload.assigned_feature_scope == "both"


def test_camera_management_is_common_but_processing_keeps_attendance_guard() -> None:
    assert cameras.router.dependencies == []

    process_route = next(
        route
        for route in cameras.router.routes
        if isinstance(route, APIRoute) and route.path == "/{camera_id}/process-frame"
    )
    dependency_names = {dependency.name for dependency in process_route.dependant.dependencies}

    assert "current_admin" in dependency_names
    assert "_attendance_access" in dependency_names
