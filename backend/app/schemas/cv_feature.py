"""Master CV feature schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CvFeatureRead(BaseModel):
    id: str
    feature_name: str
    feature_code: str
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CvFeatureCreate(BaseModel):
    feature_name: str
    feature_code: str
    description: str | None = None
    status: str = "active"


class CvFeatureUpdate(BaseModel):
    feature_name: str | None = None
    feature_code: str | None = None
    description: str | None = None
    status: str | None = None


class CvFeatureListResponse(BaseModel):
    features: list[CvFeatureRead]
