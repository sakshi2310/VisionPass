"""Download and validate the configured InsightFace model before API startup."""

from __future__ import annotations

from app.core.config import settings


def main() -> int:
    from insightface.app import FaceAnalysis

    analyzer = FaceAnalysis(
        name=settings.face_model_name,
        allowed_modules=["detection", "recognition"],
        providers=["CPUExecutionProvider"],
    )
    analyzer.prepare(ctx_id=-1, det_thresh=settings.face_detection_confidence, det_size=(320, 320))
    print(f"InsightFace model '{settings.face_model_name}' is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
