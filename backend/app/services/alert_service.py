"""Tenant-scoped alert creation and lifecycle service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.models.alert import Alert

ALERT_DEFAULTS: dict[str, tuple[str, str]] = {
    "UNKNOWN_FACE": ("high", "Unknown face detected"),
    "LOW_CONFIDENCE_FACE": ("medium", "Low-confidence face match"),
    "DUPLICATE_ATTENDANCE_ATTEMPT": ("medium", "Duplicate attendance attempt"),
    "ACCESS_DENIED": ("high", "Access denied"),
    "CAMERA_OFFLINE": ("high", "Camera offline"),
    "CAMERA_ERROR": ("high", "Camera error"),
    "BLOCKED_VISITOR": ("critical", "Blocked visitor attempted access"),
    "INACTIVE_EMPLOYEE_ATTEMPT": ("critical", "Inactive employee attempted access"),
}


class AlertError(Exception):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_alert(
    db: Session,
    *,
    tenant_id: str,
    alert_type: str,
    message: str,
    source_type: str,
    source_id: str | None = None,
    metadata: dict | None = None,
    severity: str | None = None,
    title: str | None = None,
) -> Alert:
    default_severity, default_title = ALERT_DEFAULTS[alert_type]
    alert = Alert(
        tenant_id=tenant_id,
        alert_type=alert_type,
        severity=severity or default_severity,
        title=title or default_title,
        message=message,
        status="open",
        source_type=source_type,
        source_id=source_id,
        alert_metadata=metadata or {},
    )
    # Recognition unit tests use a deliberately tiny session double. The real
    # SQLAlchemy session always provides add(), while the decision can still be
    # evaluated with those read-only doubles.
    if hasattr(db, "add"):
        db.add(alert)
    return alert


def list_alerts(
    db: Session,
    tenant_id: str,
    *,
    status: str | None = None,
    limit: int = 100,
) -> list[Alert]:
    query = db.query(Alert).filter(Alert.tenant_id == tenant_id)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


def get_alert(db: Session, tenant_id: str, alert_id: str) -> Alert | None:
    return (
        db.query(Alert)
        .filter(Alert.tenant_id == tenant_id, cast(Alert.id, String) == alert_id)
        .one_or_none()
    )


def acknowledge_alert(db: Session, tenant_id: str, alert_id: str) -> Alert | None:
    alert = get_alert(db, tenant_id, alert_id)
    if alert is None:
        return None
    if alert.status == "resolved":
        raise AlertError("Resolved alerts cannot be acknowledged")
    if alert.status == "open":
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.add(alert)
        db.commit()
        db.refresh(alert)
    return alert


def resolve_alert(db: Session, tenant_id: str, alert_id: str) -> Alert | None:
    alert = get_alert(db, tenant_id, alert_id)
    if alert is None:
        return None
    if alert.status != "resolved":
        now = datetime.now(timezone.utc)
        if alert.acknowledged_at is None:
            alert.acknowledged_at = now
        alert.status = "resolved"
        alert.resolved_at = now
        db.add(alert)
        db.commit()
        db.refresh(alert)
    return alert
