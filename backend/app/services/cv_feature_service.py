"""Master feature service."""

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.models.feature import Feature
from app.models.member_feature import MemberFeature
from app.models.tenant_feature import TenantFeature

logger = get_logger("features")

DEFAULT_MASTER_FEATURES = [
    ("Face Recognition", "face_recognition", "Recognize enrolled faces at access points.", "active"),
    ("Attendance", "attendance", "Daily check-ins and attendance logs.", "active"),
    ("Visitor Management", "visitor_management", "Track and classify visitors.", "active"),
    ("ANPR", "anpr", "Automatic number plate recognition.", "active"),
    ("PPE Detection", "ppe_detection", "Detect safety equipment compliance.", "active"),
    ("Crowd Detection", "crowd_detection", "Detect crowding and occupancy spikes.", "active"),
    ("Object Detection", "object_detection", "Detect configured objects in live video.", "active"),
    ("Emotion Analytics", "emotion_analytics", "Analyze facial emotion signals.", "active"),
    ("Intrusion Detection", "intrusion_detection", "Detect restricted-area intrusion events.", "active"),
    ("Live Feed", "live_feed", "Stream live video feeds.", "active"),
    ("Reports", "reports", "Generate downloadable platform reports.", "active"),
]


def seed_default_master_features(db: Session) -> None:
    existing_codes = {code for (code,) in db.query(Feature.feature_code).all()}
    created = False
    for feature_name, feature_code, description, status in DEFAULT_MASTER_FEATURES:
        if feature_code in existing_codes:
            continue
        db.add(
            Feature(
                feature_name=feature_name,
                feature_code=feature_code,
                description=description,
                status=status,
            )
        )
        created = True
    if created:
        db.commit()


def list_master_features(db: Session, include_deleted: bool = False) -> list[Feature]:
    query = db.query(Feature)
    query = query.filter(Feature.is_deleted.is_(False))
    if not include_deleted:
        query = query.filter(Feature.status == "active")
    return query.order_by(Feature.created_at.desc()).all()


def list_active_master_features(db: Session) -> list[Feature]:
    return (
        db.query(Feature)
        .filter(Feature.is_deleted.is_(False))
        .filter(Feature.status == "active")
        .order_by(Feature.created_at.desc())
        .all()
    )


def list_active_feature_codes(db: Session) -> list[str]:
    return [feature.feature_code for feature in list_active_master_features(db)]


def get_master_feature(db: Session, feature_id: str) -> Feature | None:
    return (
        db.query(Feature)
        .filter(Feature.id == feature_id, Feature.is_deleted.is_(False))
        .one_or_none()
    )


def create_master_feature(
    db: Session,
    *,
    feature_name: str,
    feature_code: str,
    description: str | None,
    status: str,
) -> Feature:
    normalized_code = feature_code.strip().lower()
    existing = db.query(Feature).filter(Feature.feature_code == normalized_code).one_or_none()
    if existing is not None:
        raise ValueError("Feature code already exists")

    logger.info(f'>>> CREATE MASTER FEATURE -- Code: {normalized_code} | Name: "{feature_name}"')
    feature = Feature(
        feature_name=feature_name.strip(),
        feature_code=normalized_code,
        description=description.strip() if description else None,
        status=status,
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    logger.info(f'OK MASTER FEATURE CREATED -- ID: {feature.id} | Code: {feature.feature_code}')
    return feature


def update_master_feature(
    db: Session,
    feature_id: str,
    *,
    feature_name: str | None = None,
    feature_code: str | None = None,
    description: str | None = None,
    status: str | None = None,
) -> Feature | None:
    feature = get_master_feature(db, feature_id)
    if feature is None:
        return None

    if feature_code is not None:
        normalized_code = feature_code.strip().lower()
        existing = (
            db.query(Feature)
            .filter(Feature.feature_code == normalized_code, Feature.id != feature.id)
            .one_or_none()
        )
        if existing is not None:
            raise ValueError("Feature code already exists")
        feature.feature_code = normalized_code
    if feature_name is not None:
        feature.feature_name = feature_name.strip()
    if description is not None:
        feature.description = description.strip() or None
    if status is not None:
        feature.status = status

    db.commit()
    db.refresh(feature)
    logger.info(f'OK MASTER FEATURE UPDATED -- ID: {feature.id} | Code: {feature.feature_code}')
    return feature


def delete_master_feature(db: Session, feature_id: str) -> bool:
    feature = get_master_feature(db, feature_id)
    if feature is None:
        return False

    logger.warning(f'>>> DELETE MASTER FEATURE -- Code: {feature.feature_code} | ID: {feature.id}')
    db.query(MemberFeature).filter(
        MemberFeature.feature_code == feature.feature_code
    ).delete(synchronize_session=False)
    db.query(TenantFeature).filter(
        TenantFeature.feature_code == feature.feature_code
    ).delete(synchronize_session=False)
    feature.status = "inactive"
    feature.is_deleted = True
    db.add(feature)
    db.commit()
    logger.warning(f'WARN MASTER FEATURE DELETED -- ID: {feature_id}')
    return True
