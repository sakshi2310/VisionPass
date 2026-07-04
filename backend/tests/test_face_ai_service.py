"""Unit tests for trusted server-side face image validation."""

from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from app.services.face_ai_service import (
    INVALID_IMAGE,
    LOW_FACE_CONFIDENCE,
    LOW_IMAGE_QUALITY,
    MULTIPLE_FACES_DETECTED,
    NO_FACE_DETECTED,
    FaceValidationError,
    analyze_face_image,
)


def _sharp_image_bytes() -> bytes:
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    image[::2, ::2] = 220
    image[1::2, 1::2] = 220
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    return encoded.tobytes()


def _encoded_image(image: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    return encoded.tobytes()


def _face(*, confidence: float = 0.99):
    return SimpleNamespace(
        det_score=confidence,
        bbox=np.array([150, 80, 470, 400], dtype=np.float32),
        normed_embedding=np.ones(512, dtype=np.float32),
    )


def _analyze(analyzer):
    return analyze_face_image(
        _sharp_image_bytes(),
        min_resolution_width=320,
        min_resolution_height=240,
        min_face_size_px=64,
        min_sharpness_score=120,
        min_brightness=35,
        max_brightness=220,
        analyzer=analyzer,
    )


def test_rejects_unreadable_image():
    with pytest.raises(FaceValidationError) as error:
        analyze_face_image(
            b"not an image",
            min_resolution_width=320,
            min_resolution_height=240,
            min_face_size_px=64,
            min_sharpness_score=120,
            min_brightness=35,
            max_brightness=220,
            analyzer=SimpleNamespace(get=lambda _: []),
        )

    assert error.value.code == INVALID_IMAGE


def test_rejects_missing_and_multiple_faces():
    with pytest.raises(FaceValidationError) as no_face:
        _analyze(SimpleNamespace(get=lambda _: []))
    assert no_face.value.code == NO_FACE_DETECTED

    with pytest.raises(FaceValidationError) as multiple:
        _analyze(SimpleNamespace(get=lambda _: [_face(), _face()]))
    assert multiple.value.code == MULTIPLE_FACES_DETECTED


def test_rejects_low_confidence_face():
    with pytest.raises(FaceValidationError) as error:
        _analyze(SimpleNamespace(get=lambda _: [_face(confidence=0.20)]))

    assert error.value.code == LOW_FACE_CONFIDENCE


@pytest.mark.parametrize(
    ("content", "face"),
    [
        (_encoded_image(np.full((100, 100, 3), 120, dtype=np.uint8)), _face()),
        (_encoded_image(np.full((480, 640, 3), 120, dtype=np.uint8)), _face()),
        (_sharp_image_bytes(), SimpleNamespace(
            det_score=0.99,
            bbox=np.array([20, 20, 60, 60], dtype=np.float32),
            normed_embedding=np.ones(512, dtype=np.float32),
        )),
    ],
    ids=["low-resolution", "blurry", "face-too-small"],
)
def test_rejects_low_resolution_blur_and_small_faces(content, face):
    with pytest.raises(FaceValidationError) as error:
        analyze_face_image(
            content,
            min_resolution_width=320,
            min_resolution_height=240,
            min_face_size_px=64,
            min_sharpness_score=120,
            min_brightness=35,
            max_brightness=220,
            analyzer=SimpleNamespace(get=lambda _: [face]),
        )

    assert error.value.code == LOW_IMAGE_QUALITY


def test_returns_real_model_embedding_and_server_metrics():
    result = _analyze(SimpleNamespace(get=lambda _: [_face()]))

    assert len(result.embedding) == 512
    assert np.linalg.norm(result.embedding) == pytest.approx(1.0)
    assert result.face_count == 1
    assert result.detection_confidence == pytest.approx(0.99)
    assert result.quality_score >= 0.70
