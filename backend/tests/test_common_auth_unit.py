"""Fast unit checks for the common authentication contract."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.schemas.auth import AuthResponse, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import authenticate_login


def test_common_login_uses_super_admin_authenticator():
    db = Mock()
    admin = Mock()

    with (
        patch("app.services.auth_service._find_super_admin_by_email", return_value=admin),
        patch("app.services.auth_service.authenticate_super_admin_login", return_value=admin),
        patch("app.services.auth_service.authenticate_tenant_member_login") as tenant_login,
    ):
        tenant, account = authenticate_login(db, "admin@example.test", "password")

    assert tenant is None
    assert account is admin
    tenant_login.assert_not_called()


def test_common_login_falls_back_to_tenant_member():
    db = Mock()
    tenant = Mock()
    member = Mock()

    with (
        patch("app.services.auth_service._find_super_admin_by_email", return_value=None),
        patch(
            "app.services.auth_service.authenticate_tenant_member_login",
            return_value=(tenant, member),
        ),
    ):
        authenticated_tenant, account = authenticate_login(
            db,
            "member@example.test",
            "password",
        )

    assert authenticated_tenant is tenant
    assert account is member


def test_auth_response_exposes_compatible_top_level_token():
    now = datetime.now(timezone.utc)
    user = UserRead(
        id="admin-id",
        email="admin@example.test",
        full_name="Admin",
        role="super_admin",
        tenant_id=None,
        created_at=now,
        updated_at=now,
    )

    payload = AuthResponse(
        token=TokenResponse(access_token="test-token"),
        user=user,
    ).model_dump()

    assert payload["access_token"] == payload["token"]["access_token"] == "test-token"
    assert payload["token_type"] == "bearer"
