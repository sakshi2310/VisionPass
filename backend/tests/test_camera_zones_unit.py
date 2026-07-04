"""Database-free camera detection-zone schema checks."""

import pytest
from pydantic import ValidationError

from app.schemas.camera import CameraCreate, CameraUpdate


def test_camera_create_accepts_detection_zones() -> None:
    camera = CameraCreate(
        name="Loading bay",
        location="Warehouse",
        camera_type="http_mjpeg",
        stream_url="http://192.168.1.25:8080/video",
        assigned_feature_scope="object_detection",
        detection_zones=[
            {"id": "loading-zone", "name": "Loading zone", "x": 10, "y": 15, "width": 45, "height": 50}
        ],
    )

    assert camera.detection_zones[0].name == "Loading zone"
    assert camera.detection_zones[0].width == 45


def test_camera_update_rejects_out_of_range_zone_coordinates() -> None:
    with pytest.raises(ValidationError):
        CameraUpdate(
            detection_zones=[
                {"id": "invalid", "name": "Invalid", "x": 101, "y": 0, "width": 20, "height": 20}
            ]
        )
