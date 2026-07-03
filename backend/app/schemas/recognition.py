"""Face recognition request and response schemas."""

from typing import Literal

from pydantic import BaseModel, model_validator


RecognitionMode = Literal["attendance", "access", "visitor"]
RecognitionStatus = Literal[
    "MATCHED",
    "UNKNOWN",
    "LOW_CONFIDENCE",
    "NO_FACE",
    "MULTIPLE_FACES",
]


class RecognitionBase64Request(BaseModel):
    image: str | None = None
    base64_frame: str | None = None
    camera_id: str | None = None
    mode: RecognitionMode = "attendance"

    @model_validator(mode="after")
    def require_one_frame(self):
        if not (self.image or self.base64_frame):
            raise ValueError("image or base64_frame is required")
        return self

    @property
    def frame(self) -> str:
        return self.image or self.base64_frame or ""


class RecognitionResponse(BaseModel):
    recognized: bool
    employee_id: str | None = None
    employee_name: str | None = None
    confidence: float | None = None
    distance: float | None = None
    threshold: float
    recognition_status: RecognitionStatus
