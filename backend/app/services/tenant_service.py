"""Tenant service."""

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.models.tenant import Tenant

logger = get_logger("tenants")


def get_tenant_by_slug(db: Session, slug: str) -> Tenant | None:
    return db.query(Tenant).filter(Tenant.slug == slug, Tenant.is_deleted.is_(False)).one_or_none()


def _tenant_slug_exists(db: Session, slug: str) -> bool:
    """Include soft-deleted tenants because the database slug constraint is global."""
    return db.query(Tenant.id).filter(Tenant.slug == slug).limit(1).one_or_none() is not None


def create_tenant(
    db: Session,
    name: str,
    slug: str,
    status: str = "active",
    plan: str = "basic",
    industry: str = "General",
    max_users: int = 100,
    max_devices: int = 20,
    company_email: str | None = None,
    logo_url: str | None = None,
    address: str | None = None,
) -> Tenant:
    base_slug = slug.strip() or "visionpass-platform"
    candidate_slug = base_slug
    suffix = 2
    while _tenant_slug_exists(db, candidate_slug):
        candidate_slug = f"{base_slug}-{suffix}"
        suffix += 1

    tenant = Tenant(
        name=name,
        slug=candidate_slug,
        status=status,
        plan=plan,
        industry=industry,
        max_users=max_users,
        max_devices=max_devices,
        company_email=company_email.lower().strip() if company_email else None,
        logo_url=logo_url,
        address=address,
    )
    db.add(tenant)
    db.flush()
    logger.info(f'>>> CREATE TENANT REQUEST -- Org Name: "{tenant.name}" | Slug: {candidate_slug} | Status: {status}')
    logger.info(f'OK TENANT CREATED -- ID: {tenant.id} | Org: "{tenant.name}"')
    return tenant
