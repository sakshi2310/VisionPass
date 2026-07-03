"""Server-side face detection, image quality validation, and embedding extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any

from app.core.config import settings

NO_FACE_DETECTED = "NO_FACE_DETECTED"
MULTIPLE_FACES_DETECTED = "MULTIPLE_FACES_DETECTED"
LOW_FACE_CONFIDENCE = "LOW_FACE_CONFIDENCE"
LOW_IMAGE_QUALITY = "LOW_IMAGE_QUALITY"
INVALID_IMAGE = "INVALID_IMAGE"
DUPLICATE_FACE_DETECTED = "DUPLICATE_FACE_DETECTED"


@dataclass(frozen=True)
class UploadedFaceImage:
    """Untrusted image bytes received by an enrollment endpoint."""

    content: bytes
    filename: str
    content_type: str


@dataclass(frozen=True)
class FaceAnalysisResult:
    """Trusted measurements produced by server-side image analysis."""

    embedding: list[float]
    detection_confidence: float
    quality_score: float
    width: int
    height: int
    face_count: int
    face_bbox: tuple[int, int, int, int]
    face_size_px: int
    blur_score: float
    brightness: float


class FaceValidationError(ValueError):
    """An image failed a specific, user-correctable validation rule."""

    def __init__(self, code: str, message: str, **metrics: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.metrics = metrics

    def as_dict(self, *, filename: str | None = None) -> dict[str, Any]:
        return {
            "filename": filename,
            "status": "Failed",
            "enrollment_status": "rejected",
            "code": self.code,
            "message": self.message,
            **self.metrics,
        }


class FaceModelUnavailableError(RuntimeError):
    """The local face model could not be initialized."""


@lru_cache(maxsize=1)
def _get_face_analyzer():
    """Load InsightFace lazily so ordinary API startup does not load the model."""

    try:
        from insightface.app import FaceAnalysis

        analyzer = FaceAnalysis(
            name=settings.face_model_name,
            providers=["CPUExecutionProvider"],
        )
        # Detect at a permissive floor, then enforce the configured confidence
        # ourselves so low-confidence faces return a precise API error.
        analyzer.prepare(ctx_id=-1, det_thresh=0.01, det_size=(640, 640))
        return analyzer
    except Exception as exc:  # pragma: no cover - depends on local model/runtime
        raise FaceModelUnavailableError(
            f"Unable to initialize InsightFace model '{settings.face_model_name}'."
        ) from exc


def _decode_image(content: bytes):
    try:
        import cv2
        import numpy as np

        encoded = np.frombuffer(content, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except Exception as exc:
        raise FaceValidationError(INVALID_IMAGE, "The uploaded file is not a readable image.") from exc
    if image is None or image.size == 0:
        raise FaceValidationError(INVALID_IMAGE, "The uploaded file is not a readable image.")
    return image


def analyze_face_image(
    content: bytes,
    *,
    min_resolution_width: int,
    min_resolution_height: int,
    min_face_size_px: int,
    min_sharpness_score: float,
    min_brightness: float,
    max_brightness: float,
    analyzer=None,
) -> FaceAnalysisResult:
    """Validate one image and return its real InsightFace embedding."""

    import cv2
    import numpy as np

    if not content:
        raise FaceValidationError(INVALID_IMAGE, "The uploaded image is empty.")

    image = _decode_image(content)
    height, width = image.shape[:2]
    if width < min_resolution_width or height < min_resolution_height:
        raise FaceValidationError(
            LOW_IMAGE_QUALITY,
            f"Image resolution must be at least {min_resolution_width} x {min_resolution_height}.",
            width=width,
            height=height,
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if not min_brightness <= brightness <= max_brightness:
        raise FaceValidationError(
            LOW_IMAGE_QUALITY,
            "The image is too dark or too bright. Use even, front-facing light.",
            brightness=round(brightness, 2),
        )
    # This legacy database field is named max_blur_score, but stores the
    # minimum acceptable Laplacian variance: larger values are sharper.
    if blur_score < min_sharpness_score:
        raise FaceValidationError(
            LOW_IMAGE_QUALITY,
            "The face image is blurry. Hold the camera steady and try again.",
            blur_score=round(blur_score, 2),
        )

    detector = analyzer or _get_face_analyzer()
    faces = detector.get(image)
    if not faces:
        raise FaceValidationError(NO_FACE_DETECTED, "No face was detected in the image.")
    if len(faces) > 1:
        raise FaceValidationError(
            MULTIPLE_FACES_DETECTED,
            "Multiple faces were detected. Upload an image containing one person only.",
            face_count=len(faces),
        )

    face = faces[0]
    confidence = float(face.det_score)
    if confidence < settings.face_detection_confidence:
        raise FaceValidationError(
            LOW_FACE_CONFIDENCE,
            "The detected face is not clear enough. Face the camera and improve the lighting.",
            detection_confidence=round(confidence, 4),
        )

    x1, y1, x2, y2 = (int(round(float(value))) for value in face.bbox)
    face_width = max(0, x2 - x1)
    face_height = max(0, y2 - y1)
    face_size = min(face_width, face_height)
    if face_size < min_face_size_px:
        raise FaceValidationError(
            LOW_IMAGE_QUALITY,
            f"The face is too small. It must be at least {min_face_size_px}px in both dimensions.",
            face_size_px=face_size,
        )

    sharpness_quality = min(blur_score / max(min_sharpness_score * 4, 1.0), 1.0)
    face_size_quality = min(face_size / max(min_face_size_px * 2, 1), 1.0)
    resolution_quality = min(
        width / max(min_resolution_width * 2, 1),
        height / max(min_resolution_height * 2, 1),
        1.0,
    )
    brightness_midpoint = (min_brightness + max_brightness) / 2
    brightness_radius = max((max_brightness - min_brightness) / 2, 1.0)
    brightness_quality = max(
        0.0,
        1.0 - abs(brightness - brightness_midpoint) / brightness_radius,
    )
    quality_score = (
        0.35 * confidence
        + 0.2 * sharpness_quality
        + 0.2 * face_size_quality
        + 0.15 * brightness_quality
        + 0.1 * resolution_quality
    )
    if quality_score < settings.face_enrollment_min_quality:
        raise FaceValidationError(
            LOW_IMAGE_QUALITY,
            "The overall face image quality is too low for enrollment.",
            quality_score=round(quality_score, 4),
        )

    raw_embedding = getattr(face, "normed_embedding", None)
    if raw_embedding is None:
        raw_embedding = getattr(face, "embedding", None)
    if raw_embedding is None:
        raise FaceValidationError(INVALID_IMAGE, "The face model could not generate an embedding.")
    embedding_array = np.asarray(raw_embedding, dtype=np.float32).reshape(-1)
    if len(embedding_array) != 512:
        raise FaceValidationError(
            INVALID_IMAGE,
            "The configured face model returned an unsupported embedding size.",
            embedding_dimension=len(embedding_array),
        )
    embedding_norm = float(np.linalg.norm(embedding_array))
    if not np.isfinite(embedding_norm) or embedding_norm <= 1e-12:
        raise FaceValidationError(INVALID_IMAGE, "The face model returned an invalid embedding.")
    # Normalize explicitly even when InsightFace exposes normed_embedding.
    # This keeps storage and duplicate comparisons consistent across models.
    embedding = (embedding_array / embedding_norm).tolist()

    return FaceAnalysisResult(
        embedding=[float(value) for value in embedding],
        detection_confidence=confidence,
        quality_score=quality_score,
        width=width,
        height=height,
        face_count=1,
        face_bbox=(x1, y1, x2, y2),
        face_size_px=face_size,
        blur_score=blur_score,
        brightness=brightness,
    )


def successful_validation(filename: str, result: FaceAnalysisResult) -> dict[str, Any]:
    """Build the public validation result without exposing the embedding."""

    metrics = asdict(result)
    metrics.pop("embedding")
    return {
        "filename": filename,
        "status": "Validated",
        "enrollment_status": "valid",
        "code": None,
        "message": "One clear face was detected and validated.",
        **metrics,
    }
