"""Database-free regression tests for disable versus delete semantics."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.feature import Feature
from app.models.member_feature import MemberFeature
from app.models.tenant_feature import TenantFeature
from app.api.v1.endpoints import super_admin
from app.services import cv_feature_service


def test_disable_keeps_feature_record_as_inactive(monkeypatch) -> None:
    db = MagicMock()
    feature = SimpleNamespace(id="feature-1", feature_code="attendance", status="active")
    monkeypatch.setattr(cv_feature_service, "get_master_feature", lambda *_: feature)

    updated = cv_feature_service.update_master_feature(
        db,
        feature.id,
        status="inactive",
    )

    assert updated is feature
    assert feature.status == "inactive"
    db.delete.assert_not_called()
    db.commit.assert_called_once()


def test_delete_removes_feature_and_all_code_assignments(monkeypatch) -> None:
    db = MagicMock()
    feature = SimpleNamespace(id="feature-1", feature_code="attendance", status="active", is_deleted=False)
    monkeypatch.setattr(cv_feature_service, "get_master_feature", lambda *_: feature)

    assert cv_feature_service.delete_master_feature(db, feature.id) is True

    queried_models = [call.args[0] for call in db.query.call_args_list]
    assert queried_models == [MemberFeature, TenantFeature]
    assert db.query.return_value.filter.return_value.delete.call_count == 2
    assert feature.status == "inactive"
    assert feature.is_deleted is True
    db.add.assert_called_once_with(feature)
    db.delete.assert_not_called()
    db.commit.assert_called_once()


def test_deleted_feature_returns_false_when_missing(monkeypatch) -> None:
    db = MagicMock()
    monkeypatch.setattr(cv_feature_service, "get_master_feature", lambda *_: None)

    assert cv_feature_service.delete_master_feature(db, "missing") is False
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_super_admin_list_requests_inactive_features(monkeypatch) -> None:
    captured: dict[str, bool] = {}

    def fake_list(_db, *, include_deleted: bool):
        captured["include_deleted"] = include_deleted
        return []

    monkeypatch.setattr(super_admin, "list_master_features", fake_list)

    response = super_admin.get_features(db=MagicMock(), _=None)

    assert response.features == []
    assert captured["include_deleted"] is True
