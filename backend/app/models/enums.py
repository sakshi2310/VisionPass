"""Shared PostgreSQL enum helpers."""

from sqlalchemy import Enum

ACCOUNT_STATUS_VALUES = ("active", "inactive", "suspended")
MEMBER_ROLE_VALUES = ("tenant_admin", "user")

account_status_enum = Enum(
    *ACCOUNT_STATUS_VALUES,
    name="account_status",
    create_type=False,
)

member_role_enum = Enum(
    *MEMBER_ROLE_VALUES,
    name="member_role",
    create_type=False,
)
