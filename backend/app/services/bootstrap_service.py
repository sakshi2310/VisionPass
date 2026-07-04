"""Application bootstrap helpers and idempotent MVP demo data."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.access_event import AccessLog
from app.models.alert import Alert
from app.models.attendance import AttendanceEvent, AttendanceHoliday, AttendanceShift, DailyAttendanceRecord
from app.models.camera import Camera, CameraEvent
from app.models.employee import AttendanceEmployee
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant
from app.models.tenant_feature import TenantFeature
from app.models.tenant_member import TenantMember
from app.models.member_feature import MemberFeature
from app.models.visitor import Visitor, VisitorVisit
from app.services.cv_feature_service import list_active_feature_codes, seed_default_master_features
from app.services.feature_flag_service import set_member_modules, set_tenant_modules
from app.services.tenant_service import create_tenant

DEMO_SUPER_ADMIN_EMAIL = "admin@gmail.com"
DEMO_SUPER_ADMIN_PASSWORD = "admin@123"
DEMO_TENANT_SLUG = "visionpass-demo"
DEMO_TENANT_NAME = "VisionPass Demo Tenant"
DEMO_TENANT_EMAIL = "contact@visionpass.test"
DEMO_TENANT_ADMIN_EMAIL = "tenant.admin@visionpass.test"
DEMO_TENANT_ADMIN_PASSWORD = "TenantAdmin@123"
DEMO_TENANT_USER_EMAIL = "normal.user@visionpass.test"
DEMO_TENANT_USER_PASSWORD = "User@123456"
DEMO_FEATURE_CODES = [
    "face_recognition",
    "attendance",
    "visitor_management",
    "live_feed",
    "reports",
    "intrusion_detection",
]
DEMO_USER_FEATURE_CODES = ["face_recognition", "attendance"]
DEMO_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _upsert_super_admin(db: Session) -> SuperAdmin:
    admin = db.query(SuperAdmin).filter(SuperAdmin.email == DEMO_SUPER_ADMIN_EMAIL).one_or_none()
    if admin is not None:
        return admin

    admin = SuperAdmin(
        email=DEMO_SUPER_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_SUPER_ADMIN_PASSWORD),
        full_name="Super Admin",
        status="active",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _upsert_demo_tenant(db: Session) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == DEMO_TENANT_SLUG).one_or_none()
    if tenant is not None:
        tenant.name = DEMO_TENANT_NAME
        tenant.company_email = DEMO_TENANT_EMAIL
        tenant.status = "active"
        tenant.is_deleted = False
        tenant.industry = "Security"
        tenant.address = "Demo Campus"
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant

    tenant = create_tenant(
        db=db,
        name=DEMO_TENANT_NAME,
        slug=DEMO_TENANT_SLUG,
        status="active",
        plan="basic",
        industry="Security",
        company_email=DEMO_TENANT_EMAIL,
        max_users=100,
        max_devices=20,
        address="Demo Campus",
    )
    db.commit()
    db.refresh(tenant)
    return tenant


def _get_or_create_shift(db: Session, tenant_id: str) -> AttendanceShift:
    shift = (
        db.query(AttendanceShift)
        .filter(AttendanceShift.tenant_id == tenant_id, AttendanceShift.name == "General Shift")
        .one_or_none()
    )
    if shift is None:
        shift = AttendanceShift(
            tenant_id=tenant_id,
            name="General Shift",
            start_time=time(9, 0),
            end_time=time(18, 0),
            grace_period_minutes=10,
            late_after_minutes=10,
            half_day_min_minutes=240,
            full_day_min_minutes=480,
            auto_checkout_time=time(20, 0),
            break_duration_minutes=60,
            is_default=True,
            is_active=True,
        )
        db.add(shift)
        db.flush()
    return shift


def _get_or_create_employee(
    db: Session,
    tenant_id: str,
    shift_id: str,
    *,
    code: str,
    name: str,
    email: str,
    department: str,
    designation: str,
) -> AttendanceEmployee:
    employee = (
        db.query(AttendanceEmployee)
        .filter(
            AttendanceEmployee.tenant_id == tenant_id,
            AttendanceEmployee.employee_code == code,
        )
        .one_or_none()
    )
    if employee is None:
        employee = AttendanceEmployee(
            tenant_id=tenant_id,
            employee_code=code,
            full_name=name,
            email=email,
            department=department,
            designation=designation,
            shift_id=shift_id,
            joining_date=date(2025, 1, 6),
            employee_type="Full Time",
            is_active=True,
        )
        db.add(employee)
        db.flush()
    return employee


def _get_or_create_camera(
    db: Session,
    tenant_id: str,
    *,
    name: str,
    location: str,
) -> Camera:
    camera = (
        db.query(Camera)
        .filter(Camera.tenant_id == tenant_id, Camera.name == name)
        .one_or_none()
    )
    if camera is None:
        camera = Camera(
            tenant_id=tenant_id,
            name=name,
            location=location,
            camera_type="manual",
            is_active=True,
            health_status="online",
        )
        db.add(camera)
        db.flush()
    return camera


def _seed_attendance_day(
    db: Session,
    tenant_id: str,
    employee: AttendanceEmployee,
    shift: AttendanceShift,
    camera: Camera,
    attendance_date: date,
    *,
    check_in_at: time | None,
    check_out_at: time | None,
    status: str,
    total_work_minutes: int,
) -> None:
    first_check_in = (
        datetime.combine(attendance_date, check_in_at, DEMO_TIMEZONE)
        if check_in_at is not None
        else None
    )
    last_check_out = (
        datetime.combine(attendance_date, check_out_at, DEMO_TIMEZONE)
        if check_out_at is not None
        else None
    )
    daily = (
        db.query(DailyAttendanceRecord)
        .filter(
            DailyAttendanceRecord.tenant_id == tenant_id,
            DailyAttendanceRecord.employee_id == employee.id,
            DailyAttendanceRecord.attendance_date == attendance_date,
        )
        .one_or_none()
    )
    if daily is None:
        db.add(
            DailyAttendanceRecord(
                tenant_id=tenant_id,
                employee_id=employee.id,
                attendance_date=attendance_date,
                first_check_in=first_check_in,
                last_check_out=last_check_out,
                total_work_minutes=total_work_minutes,
                status=status,
                shift_id=shift.id,
            )
        )

    for event_type, event_time in (("check_in", first_check_in), ("check_out", last_check_out)):
        if event_time is None:
            continue
        exists = (
            db.query(AttendanceEvent.id)
            .filter(
                AttendanceEvent.tenant_id == tenant_id,
                AttendanceEvent.employee_id == employee.id,
                AttendanceEvent.event_type == event_type,
                AttendanceEvent.event_time == event_time,
            )
            .first()
        )
        if exists is None:
            db.add(
                AttendanceEvent(
                    tenant_id=tenant_id,
                    employee_id=employee.id,
                    event_type=event_type,
                    source="camera",
                    camera_id=camera.id,
                    confidence=0.96,
                    event_time=event_time,
                    event_metadata={"seeded": True, "demo": True},
                )
            )


def _seed_demo_operations(db: Session, tenant: Tenant) -> None:
    """Create realistic, non-biometric demo records without fake embeddings."""

    shift = _get_or_create_shift(db, tenant.id)
    employees = [
        _get_or_create_employee(
            db,
            tenant.id,
            shift.id,
            code="VP001",
            name="Aarav Sharma",
            email="aarav.sharma@visionpass.test",
            department="Engineering",
            designation="Software Engineer",
        ),
        _get_or_create_employee(
            db,
            tenant.id,
            shift.id,
            code="VP002",
            name="Meera Iyer",
            email="meera.iyer@visionpass.test",
            department="Operations",
            designation="Operations Manager",
        ),
        _get_or_create_employee(
            db,
            tenant.id,
            shift.id,
            code="VP003",
            name="Kabir Singh",
            email="kabir.singh@visionpass.test",
            department="Security",
            designation="Security Officer",
        ),
    ]

    holiday_date = date(2026, 8, 15)
    holiday = (
        db.query(AttendanceHoliday)
        .filter(
            AttendanceHoliday.tenant_id == tenant.id,
            AttendanceHoliday.holiday_date == holiday_date,
            AttendanceHoliday.department_id.is_(None),
            AttendanceHoliday.location_id.is_(None),
        )
        .one_or_none()
    )
    if holiday is None:
        db.add(
            AttendanceHoliday(
                tenant_id=tenant.id,
                holiday_name="Independence Day",
                holiday_date=holiday_date,
                is_active=True,
            )
        )

    lobby_camera = _get_or_create_camera(
        db,
        tenant.id,
        name="Lobby Entrance",
        location="Main Lobby",
    )
    gate_camera = _get_or_create_camera(
        db,
        tenant.id,
        name="North Gate",
        location="North Vehicle Gate",
    )

    today = datetime.now(DEMO_TIMEZONE).date()
    yesterday = today - timedelta(days=1)
    _seed_attendance_day(
        db, tenant.id, employees[0], shift, lobby_camera, today,
        check_in_at=time(8, 55), check_out_at=None, status="present", total_work_minutes=0,
    )
    _seed_attendance_day(
        db, tenant.id, employees[1], shift, lobby_camera, today,
        check_in_at=time(9, 18), check_out_at=None, status="late", total_work_minutes=0,
    )
    _seed_attendance_day(
        db, tenant.id, employees[2], shift, gate_camera, today,
        check_in_at=None, check_out_at=None, status="absent", total_work_minutes=0,
    )
    prior_times = [
        (time(8, 50), time(17, 45)),
        (time(8, 55), time(17, 50)),
        (time(9, 0), time(17, 55)),
    ]
    for employee, (check_in_at, check_out_at) in zip(employees, prior_times, strict=True):
        _seed_attendance_day(
            db, tenant.id, employee, shift, lobby_camera, yesterday,
            check_in_at=check_in_at,
            check_out_at=check_out_at,
            status="present",
            total_work_minutes=535,
        )

    recognition_time = datetime.combine(today, time(8, 55), DEMO_TIMEZONE)
    camera_event = (
        db.query(CameraEvent)
        .filter(
            CameraEvent.tenant_id == tenant.id,
            CameraEvent.camera_id == lobby_camera.id,
            CameraEvent.employee_id == employees[0].id,
            CameraEvent.created_at == recognition_time,
        )
        .one_or_none()
    )
    if camera_event is None:
        db.add(
            CameraEvent(
                tenant_id=tenant.id,
                camera_id=lobby_camera.id,
                event_type="attendance_recognition",
                employee_id=employees[0].id,
                recognition_status="MATCHED",
                confidence=0.96,
                event_metadata={"seeded": True, "demo": True},
                created_at=recognition_time,
            )
        )

    access_log = (
        db.query(AccessLog)
        .filter(
            AccessLog.tenant_id == tenant.id,
            AccessLog.employee_id == employees[0].id,
            AccessLog.camera_id == lobby_camera.id,
            AccessLog.created_at == recognition_time,
        )
        .one_or_none()
    )
    if access_log is None:
        db.add(
            AccessLog(
                tenant_id=tenant.id,
                employee_id=employees[0].id,
                camera_id=lobby_camera.id,
                decision="granted",
                reason="active_employee_within_allowed_time",
                confidence=0.96,
                created_at=recognition_time,
            )
        )

    visitor = (
        db.query(Visitor)
        .filter(Visitor.tenant_id == tenant.id, Visitor.phone == "9876500001")
        .one_or_none()
    )
    if visitor is None:
        visitor = Visitor(
            tenant_id=tenant.id,
            full_name="Riya Kapoor",
            phone="9876500001",
            email="riya.kapoor@example.test",
            company="Acme Services",
            purpose="Vendor meeting",
            host_employee_id=employees[1].id,
            status="checked_in",
        )
        db.add(visitor)
        db.flush()
    visit = (
        db.query(VisitorVisit)
        .filter(
            VisitorVisit.tenant_id == tenant.id,
            VisitorVisit.visitor_id == visitor.id,
            VisitorVisit.check_in_time == recognition_time,
        )
        .one_or_none()
    )
    if visit is None:
        db.add(
            VisitorVisit(
                tenant_id=tenant.id,
                visitor_id=visitor.id,
                check_in_time=recognition_time,
                access_status="granted",
                notes="MVP demo visit",
            )
        )

    alert = (
        db.query(Alert)
        .filter(
            Alert.tenant_id == tenant.id,
            Alert.source_id == "mvp-demo-unknown-face",
        )
        .one_or_none()
    )
    if alert is None:
        db.add(
            Alert(
                tenant_id=tenant.id,
                alert_type="UNKNOWN_FACE",
                severity="high",
                title="Unknown person requires review",
                message="An unrecognized person was detected at the North Gate.",
                status="open",
                source_type="camera",
                source_id="mvp-demo-unknown-face",
                alert_metadata={"camera_id": gate_camera.id, "seeded": True, "demo": True},
            )
        )

    db.commit()


def _upsert_tenant_member(
    db: Session,
    *,
    tenant_id: str,
    email: str,
    full_name: str,
    password: str,
    role: str,
) -> TenantMember:
    member = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == tenant_id, TenantMember.email == email.lower().strip(), TenantMember.is_deleted.is_(False))
        .one_or_none()
    )
    if member is not None:
        member.full_name = full_name
        member.role = role
        member.status = "active"
        member.is_active = True
        member.password_hash = hash_password(password)
        db.commit()
        db.refresh(member)
        return member

    member = TenantMember(
        tenant_id=tenant_id,
        email=email.lower().strip(),
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        status="active",
        is_active=True,
        is_deleted=False,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def seed_default_admin(db: Session, *, include_operational_data: bool = True) -> None:
    seed_default_master_features(db)
    _upsert_super_admin(db)
    tenant = _upsert_demo_tenant(db)
    tenant_admin = _upsert_tenant_member(
        db,
        tenant_id=tenant.id,
        email=DEMO_TENANT_ADMIN_EMAIL,
        full_name="Demo Client Admin",
        password=DEMO_TENANT_ADMIN_PASSWORD,
        role="tenant_admin",
    )
    tenant_user = _upsert_tenant_member(
        db,
        tenant_id=tenant.id,
        email=DEMO_TENANT_USER_EMAIL,
        full_name="Demo Tenant User",
        password=DEMO_TENANT_USER_PASSWORD,
        role="user",
    )

    active_feature_codes = set(list_active_feature_codes(db))
    tenant_feature_codes = [code for code in DEMO_FEATURE_CODES if code in active_feature_codes]
    user_feature_codes = [code for code in DEMO_USER_FEATURE_CODES if code in active_feature_codes]
    set_tenant_modules(db, tenant.id, tenant_feature_codes, updated_by=tenant_admin.id)
    set_member_modules(db, tenant.id, tenant_admin.id, tenant_feature_codes, updated_by=tenant_admin.id)
    set_member_modules(db, tenant.id, tenant_user.id, user_feature_codes, updated_by=tenant_admin.id)
    if include_operational_data:
        _seed_demo_operations(db, tenant)
