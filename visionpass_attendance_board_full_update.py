from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8-sig')


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


def replace_once(content: str, old: str, new: str, path: str) -> str:
    if old not in content:
        raise SystemExit(f"Could not update {path}: expected block was not found.")
    return content.replace(old, new, 1)

# 1) Backend service: add Attendance Board query helpers.
service_path = 'backend/app/services/attendance_service.py'
service = read(service_path)
if 'def get_attendance_board(' not in service:
    service += r'''


def _parse_attendance_board_date(value: date | str | None, tenant_zone: ZoneInfo) -> date:
    if value is None:
        return datetime.now(timezone.utc).astimezone(tenant_zone).date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _combine_local_datetime(attendance_date: date, value: time | None, tenant_zone: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(attendance_date, value, tzinfo=tenant_zone)


def _selected_day_bounds(attendance_date: date, tenant_zone: ZoneInfo) -> tuple[datetime, datetime]:
    start_local = datetime.combine(attendance_date, time.min, tzinfo=tenant_zone)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _status_for_board(
    record: DailyAttendanceRecord | None,
    *,
    attendance_date: date,
    tenant_zone: ZoneInfo,
    shift: AttendanceShift | None,
    now_utc: datetime,
) -> str:
    if record is not None:
        return record.status
    if _is_holiday.__name__:
        # Holiday calculation needs db, so holiday fallback is handled by get_attendance_board.
        pass
    if attendance_date < now_utc.astimezone(tenant_zone).date():
        return "absent"
    if shift is None:
        return "not_detected"
    cutoff_local = _combine_local_datetime(attendance_date, shift.start_time, tenant_zone)
    if cutoff_local is None:
        return "not_detected"
    cutoff_local = cutoff_local + timedelta(minutes=shift.late_after_minutes or shift.grace_period_minutes or 0)
    return "absent" if now_utc.astimezone(tenant_zone) > cutoff_local else "not_detected"


def _daily_present_minutes(
    record: DailyAttendanceRecord | None,
    *,
    attendance_date: date,
    tenant_zone: ZoneInfo,
    now_utc: datetime,
) -> int:
    if record is None or record.first_check_in is None:
        return 0
    if record.last_check_out is not None:
        if record.total_work_minutes:
            return int(record.total_work_minutes)
        return max(0, int((record.last_check_out - record.first_check_in).total_seconds() // 60))
    if attendance_date == now_utc.astimezone(tenant_zone).date():
        return max(0, int((now_utc - record.first_check_in).total_seconds() // 60))
    return int(record.total_work_minutes or 0)


def _build_employee_sessions(events: list[AttendanceEvent], now_utc: datetime) -> list[dict]:
    sessions: list[dict] = []
    open_event: AttendanceEvent | None = None
    for event in events:
        if event.event_type == "check_in":
            if open_event is not None:
                duration = max(0, int((event.event_time - open_event.event_time).total_seconds() // 60))
                sessions.append({
                    "check_in": open_event.event_time,
                    "check_out": event.event_time,
                    "duration_minutes": duration,
                    "source": open_event.source,
                    "camera_id": open_event.camera_id,
                    "confidence": float(open_event.confidence) if open_event.confidence is not None else None,
                    "is_open": False,
                })
            open_event = event
        elif event.event_type == "check_out":
            if open_event is not None:
                duration = max(0, int((event.event_time - open_event.event_time).total_seconds() // 60))
                sessions.append({
                    "check_in": open_event.event_time,
                    "check_out": event.event_time,
                    "duration_minutes": duration,
                    "source": open_event.source,
                    "camera_id": open_event.camera_id,
                    "confidence": float(open_event.confidence) if open_event.confidence is not None else None,
                    "is_open": False,
                })
                open_event = None
    if open_event is not None:
        duration = max(0, int((now_utc - open_event.event_time).total_seconds() // 60))
        sessions.append({
            "check_in": open_event.event_time,
            "check_out": None,
            "duration_minutes": duration,
            "source": open_event.source,
            "camera_id": open_event.camera_id,
            "confidence": float(open_event.confidence) if open_event.confidence is not None else None,
            "is_open": True,
        })
    return sessions


def get_attendance_board(
    db: Session,
    tenant_id: str,
    *,
    attendance_date: date | str | None = None,
    search: str | None = None,
    department: str | None = None,
    shift_id: str | None = None,
    status_filter: str | None = None,
) -> dict:
    """Return all active employees with their date-specific attendance board status."""

    tenant_zone = _tenant_zone(db, tenant_id)
    selected_date = _parse_attendance_board_date(attendance_date, tenant_zone)
    now_utc = datetime.now(timezone.utc)
    start_utc, end_utc = _selected_day_bounds(selected_date, tenant_zone)
    is_holiday = _is_holiday(db, tenant_id, selected_date)

    employee_query = db.query(AttendanceEmployee).filter(
        AttendanceEmployee.tenant_id == tenant_id,
        AttendanceEmployee.is_active.is_(True),
    )
    if search:
        term = f"%{search.strip()}%"
        employee_query = employee_query.filter(
            or_(
                AttendanceEmployee.full_name.ilike(term),
                AttendanceEmployee.employee_code.ilike(term),
                AttendanceEmployee.email.ilike(term),
            )
        )
    if department:
        employee_query = employee_query.filter(AttendanceEmployee.department == department)
    if shift_id:
        employee_query = employee_query.filter(AttendanceEmployee.shift_id == shift_id)

    employees = employee_query.order_by(AttendanceEmployee.full_name.asc()).all()
    employee_ids = [employee.id for employee in employees]

    records = {}
    if employee_ids:
        for record in db.query(DailyAttendanceRecord).filter(
            DailyAttendanceRecord.tenant_id == tenant_id,
            DailyAttendanceRecord.attendance_date == selected_date,
            DailyAttendanceRecord.employee_id.in_(employee_ids),
        ).all():
            records[record.employee_id] = record

    shifts = {shift.id: shift for shift in db.query(AttendanceShift).filter(AttendanceShift.tenant_id == tenant_id).all()}
    default_shift = next((shift for shift in shifts.values() if shift.is_default and shift.is_active), None)

    events_by_employee: dict[str, list[AttendanceEvent]] = {employee_id: [] for employee_id in employee_ids}
    if employee_ids:
        events = db.query(AttendanceEvent).filter(
            AttendanceEvent.tenant_id == tenant_id,
            AttendanceEvent.employee_id.in_(employee_ids),
            AttendanceEvent.event_time >= start_utc,
            AttendanceEvent.event_time < end_utc,
        ).order_by(AttendanceEvent.event_time.asc()).all()
        for event in events:
            events_by_employee.setdefault(event.employee_id, []).append(event)

    rows: list[dict] = []
    stats = {"total": 0, "present": 0, "late": 0, "absent": 0, "half_day": 0, "holiday": 0, "not_detected": 0}

    for employee in employees:
        record = records.get(employee.id)
        shift = shifts.get(employee.shift_id) if employee.shift_id else default_shift
        status = "holiday" if is_holiday and record is None else _status_for_board(
            record,
            attendance_date=selected_date,
            tenant_zone=tenant_zone,
            shift=shift,
            now_utc=now_utc,
        )
        sessions = _build_employee_sessions(events_by_employee.get(employee.id, []), now_utc)
        present_minutes = _daily_present_minutes(record, attendance_date=selected_date, tenant_zone=tenant_zone, now_utc=now_utc)
        if present_minutes == 0 and sessions:
            present_minutes = sum(int(session["duration_minutes"] or 0) for session in sessions)
        expected_minutes = int(shift.full_day_min_minutes) if shift else 0
        absent_minutes = max(0, expected_minutes - present_minutes) if status in {"absent", "late", "half_day", "present", "not_detected"} else 0
        latest_event = events_by_employee.get(employee.id, [])[-1] if events_by_employee.get(employee.id) else None

        row = {
            "employee_id": employee.id,
            "employee_code": employee.employee_code,
            "employee_name": employee.full_name,
            "email": employee.email,
            "department": employee.department,
            "designation": employee.designation,
            "shift_id": employee.shift_id,
            "shift_name": shift.name if shift else None,
            "status": status,
            "first_seen_at": record.first_check_in if record else (sessions[0]["check_in"] if sessions else None),
            "last_seen_at": record.last_check_out if record and record.last_check_out else (latest_event.event_time if latest_event else None),
            "total_present_minutes": present_minutes,
            "total_absent_minutes": absent_minutes,
            "sessions_count": len(sessions),
            "latest_event_type": latest_event.event_type if latest_event else None,
            "latest_confidence": float(latest_event.confidence) if latest_event and latest_event.confidence is not None else None,
        }
        if status_filter and status_filter != "all" and row["status"] != status_filter:
            continue
        rows.append(row)
        stats["total"] += 1
        if row["status"] in stats:
            stats[row["status"]] += 1

    return {
        "attendance_date": selected_date,
        "generated_at": now_utc,
        "stats": stats,
        "employees": rows,
    }


def get_employee_attendance_summary(
    db: Session,
    tenant_id: str,
    employee_id: str,
    *,
    attendance_date: date | str | None = None,
) -> dict | None:
    tenant_zone = _tenant_zone(db, tenant_id)
    selected_date = _parse_attendance_board_date(attendance_date, tenant_zone)
    now_utc = datetime.now(timezone.utc)
    start_utc, end_utc = _selected_day_bounds(selected_date, tenant_zone)

    employee = db.query(AttendanceEmployee).filter(
        AttendanceEmployee.tenant_id == tenant_id,
        AttendanceEmployee.id == employee_id,
        AttendanceEmployee.is_active.is_(True),
    ).one_or_none()
    if employee is None:
        return None

    board = get_attendance_board(db, tenant_id, attendance_date=selected_date)
    board_row = next((row for row in board["employees"] if row["employee_id"] == employee_id), None)
    events = db.query(AttendanceEvent).filter(
        AttendanceEvent.tenant_id == tenant_id,
        AttendanceEvent.employee_id == employee_id,
        AttendanceEvent.event_time >= start_utc,
        AttendanceEvent.event_time < end_utc,
    ).order_by(AttendanceEvent.event_time.asc()).all()
    sessions = _build_employee_sessions(events, now_utc)
    detection_history = [
        {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "camera_id": event.camera_id,
            "confidence": float(event.confidence) if event.confidence is not None else None,
            "event_time": event.event_time,
            "metadata": event.event_metadata or {},
        }
        for event in events
    ]
    return {
        "attendance_date": selected_date,
        "employee": {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "employee_name": employee.full_name,
            "email": employee.email,
            "department": employee.department,
            "designation": employee.designation,
        },
        "summary": board_row,
        "sessions": sessions,
        "detection_history": detection_history,
    }
'''
    write(service_path, service)

# 2) Backend endpoint: expose board APIs under /api/client-admin/attendance.
endpoint_path = 'backend/app/api/v1/endpoints/client_admin_attendance.py'
endpoint = read(endpoint_path)
if 'get_attendance_board' not in endpoint:
    endpoint = endpoint.replace(
        'from app.services.attendance_service import (\n',
        'from app.services.attendance_service import (\n    get_attendance_board,\n    get_employee_attendance_summary,\n',
        1,
    )
if '@router.get("/board")' not in endpoint:
    marker = '@router.get("/employees", response_model=EmployeeListResponse)'
    block = r'''
@router.get("/board")
def read_attendance_board(
    date: str | None = Query(default=None),
    search: str | None = Query(default=None),
    department: str | None = Query(default=None),
    shift_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> dict:
    try:
        return get_attendance_board(
            db,
            current_admin.tenant_id,
            attendance_date=date,
            search=search,
            department=department,
            shift_id=shift_id,
            status_filter=status_filter,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/board/{employee_id}")
def read_employee_attendance_summary(
    employee_id: str,
    date: str | None = Query(default=None),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> dict:
    try:
        summary = get_employee_attendance_summary(
            db,
            current_admin.tenant_id,
            employee_id,
            attendance_date=date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return summary


'''
    endpoint = replace_once(endpoint, marker, block + marker, endpoint_path)
    write(endpoint_path, endpoint)

# 3) Frontend service types and functions.
frontend_service_path = 'frontend/src/services/clientAdminAttendance.ts'
frontend_service = read(frontend_service_path)
if 'export type AttendanceBoardStatus' not in frontend_service:
    insert_after = '''export type TodayAttendanceItem = DailyAttendance & {
  employee_name: string;
  employee_code: string;
};
'''
    addition = r'''

export type AttendanceBoardStatus = "present" | "late" | "half_day" | "absent" | "holiday" | "not_detected";

export type AttendanceBoardEmployee = {
  employee_id: string;
  employee_code: string;
  employee_name: string;
  email: string;
  department?: string | null;
  designation?: string | null;
  shift_id?: string | null;
  shift_name?: string | null;
  status: AttendanceBoardStatus;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  total_present_minutes: number;
  total_absent_minutes: number;
  sessions_count: number;
  latest_event_type?: string | null;
  latest_confidence?: number | null;
};

export type AttendanceBoardResponse = {
  attendance_date: string;
  generated_at: string;
  stats: Record<AttendanceBoardStatus | "total", number>;
  employees: AttendanceBoardEmployee[];
};

export type AttendanceSession = {
  check_in: string;
  check_out?: string | null;
  duration_minutes: number;
  source?: string | null;
  camera_id?: string | null;
  confidence?: number | null;
  is_open: boolean;
};

export type AttendanceDetectionHistory = {
  id: string;
  event_type: string;
  source: string;
  camera_id?: string | null;
  confidence?: number | null;
  event_time: string;
  metadata: Record<string, unknown>;
};

export type EmployeeAttendanceSummary = {
  attendance_date: string;
  employee: {
    id: string;
    employee_code: string;
    employee_name: string;
    email: string;
    department?: string | null;
    designation?: string | null;
  };
  summary: AttendanceBoardEmployee | null;
  sessions: AttendanceSession[];
  detection_history: AttendanceDetectionHistory[];
};
'''
    frontend_service = replace_once(frontend_service, insert_after, insert_after + addition, frontend_service_path)
if 'export async function fetchAttendanceBoard' not in frontend_service:
    marker = 'export async function fetchTodayAttendance(): Promise<TodayAttendanceItem[]> {'
    addition = r'''
export async function fetchAttendanceBoard(filters?: {
  date?: string;
  search?: string;
  department?: string;
  shiftId?: string;
  status?: string;
}): Promise<AttendanceBoardResponse> {
  const params = new URLSearchParams();
  if (filters?.date) params.set("date", filters.date);
  if (filters?.search) params.set("search", filters.search);
  if (filters?.department) params.set("department", filters.department);
  if (filters?.shiftId) params.set("shift_id", filters.shiftId);
  if (filters?.status && filters.status !== "all") params.set("status", filters.status);
  const query = params.toString();
  return requestJson<AttendanceBoardResponse>(`/api/client-admin/attendance/board${query ? `?${query}` : ""}`);
}

export function fetchEmployeeAttendanceSummary(employeeId: string, date?: string): Promise<EmployeeAttendanceSummary> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  const query = params.toString();
  return requestJson<EmployeeAttendanceSummary>(`/api/client-admin/attendance/board/${employeeId}${query ? `?${query}` : ""}`);
}

'''
    frontend_service = replace_once(frontend_service, marker, addition + marker, frontend_service_path)
    write(frontend_service_path, frontend_service)

# 4) Frontend Attendance Board page.
board_page = r'''import { CalendarDays, Clock3, Eye, Loader2, RefreshCw, Search, TimerReset, UserRoundCheck, UserRoundX, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  fetchAttendanceBoard,
  fetchEmployeeAttendanceSummary,
  fetchShifts,
  type AttendanceBoardEmployee,
  type AttendanceBoardResponse,
  type AttendanceBoardStatus,
  type EmployeeAttendanceSummary,
  type AttendanceShift,
} from "@/services/clientAdminAttendance";

const STATUS_OPTIONS: Array<{ value: "all" | AttendanceBoardStatus; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "present", label: "Present" },
  { value: "late", label: "Late" },
  { value: "half_day", label: "Half day" },
  { value: "absent", label: "Absent" },
  { value: "not_detected", label: "Not detected yet" },
  { value: "holiday", label: "Holiday" },
];

type ToastState = { tone: "success" | "error"; title: string; message: string } | null;

function todayIsoDate() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" }).format(new Date(value));
}

function formatDuration(minutes?: number | null) {
  const safe = Math.max(0, Math.round(minutes ?? 0));
  const hours = Math.floor(safe / 60);
  const remainder = safe % 60;
  return `${hours}h ${remainder}m`;
}

function statusLabel(status: AttendanceBoardStatus) {
  return status.replace("_", " ");
}

function statusTone(status: AttendanceBoardStatus) {
  if (status === "present") return "success" as const;
  if (status === "late" || status === "half_day") return "warning" as const;
  if (status === "absent") return "danger" as const;
  if (status === "holiday") return "info" as const;
  return "neutral" as const;
}

function StatCard({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
  return (
    <Card className="flex items-center justify-between p-5">
      <div>
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{value}</p>
      </div>
      <div className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-500/10 text-cyan-400">{icon}</div>
    </Card>
  );
}

function EmployeeSummaryModal({
  employee,
  date,
  onClose,
}: {
  employee: AttendanceBoardEmployee | null;
  date: string;
  onClose: () => void;
}) {
  const [summary, setSummary] = useState<EmployeeAttendanceSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!employee) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchEmployeeAttendanceSummary(employee.employee_id, date)
      .then((payload) => {
        if (!cancelled) setSummary(payload);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load employee summary.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [date, employee]);

  if (!employee) return null;

  return (
    <Modal open={Boolean(employee)} onClose={onClose} title="Employee attendance summary" size="lg">
      <div className="grid gap-5">
        <div className="flex flex-col gap-3 rounded-2xl bg-slate-50 p-4 dark:bg-white/5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white">{employee.employee_name}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {employee.employee_code} · {employee.department ?? "No department"} · {employee.shift_name ?? "No shift"}
            </p>
          </div>
          <Badge tone={statusTone(employee.status)} className="capitalize">{statusLabel(employee.status)}</Badge>
        </div>

        {loading ? (
          <div className="grid min-h-40 place-items-center text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-600 dark:text-rose-200">{error}</div>
        ) : summary ? (
          <>
            <div className="grid gap-3 sm:grid-cols-4">
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Present time</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDuration(summary.summary?.total_present_minutes)}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Absent time</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDuration(summary.summary?.total_absent_minutes)}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">First seen</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDateTime(summary.summary?.first_seen_at)}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Last seen</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDateTime(summary.summary?.last_seen_at)}</p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Presence sessions</h4>
              <div className="mt-3 overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 dark:bg-white/5">
                    <tr><th className="p-3">Check in</th><th className="p-3">Check out</th><th className="p-3">Duration</th><th className="p-3">Source</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-white/10">
                    {summary.sessions.length ? summary.sessions.map((session, index) => (
                      <tr key={`${session.check_in}-${index}`}>
                        <td className="p-3">{formatDateTime(session.check_in)}</td>
                        <td className="p-3">{session.is_open ? "Running" : formatDateTime(session.check_out)}</td>
                        <td className="p-3">{formatDuration(session.duration_minutes)}</td>
                        <td className="p-3 capitalize">{session.source ?? "—"}</td>
                      </tr>
                    )) : (
                      <tr><td className="p-4 text-center text-slate-500" colSpan={4}>No presence sessions for this date.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Detection history</h4>
              <div className="mt-3 grid gap-2">
                {summary.detection_history.length ? summary.detection_history.map((event) => (
                  <div key={event.id} className="flex items-center justify-between rounded-2xl bg-slate-50 p-3 text-sm dark:bg-white/5">
                    <span className="capitalize text-slate-700 dark:text-slate-200">{event.event_type.replace("_", " ")} · {event.source}</span>
                    <span className="text-slate-500">{formatDateTime(event.event_time)}</span>
                  </div>
                )) : <p className="text-sm text-slate-500">No detections recorded for this date.</p>}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </Modal>
  );
}

export function AttendanceBoardPage() {
  const [date, setDate] = useState(todayIsoDate());
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("");
  const [shiftId, setShiftId] = useState("");
  const [status, setStatus] = useState<"all" | AttendanceBoardStatus>("all");
  const [board, setBoard] = useState<AttendanceBoardResponse | null>(null);
  const [shifts, setShifts] = useState<AttendanceShift[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmployee, setSelectedEmployee] = useState<AttendanceBoardEmployee | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  usePageTitle("Vision Pass | Attendance Board");

  const departments = useMemo(() => {
    const values = new Set<string>();
    board?.employees.forEach((employee) => {
      if (employee.department) values.add(employee.department);
    });
    return Array.from(values).sort();
  }, [board]);

  async function loadBoard(options?: { silent?: boolean }) {
    try {
      if (!options?.silent) setLoading(true);
      const payload = await fetchAttendanceBoard({ date, search, department, shiftId, status });
      setBoard(payload);
    } catch (error) {
      setToast({ tone: "error", title: "Attendance board unavailable", message: error instanceof Error ? error.message : "Unable to load attendance board." });
    } finally {
      if (!options?.silent) setLoading(false);
    }
  }

  useEffect(() => {
    fetchShifts().then(setShifts).catch(() => setShifts([]));
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => void loadBoard(), 250);
    return () => window.clearTimeout(handle);
  }, [date, search, department, shiftId, status]);

  useEffect(() => {
    const interval = window.setInterval(() => void loadBoard({ silent: true }), 10000);
    return () => window.clearInterval(interval);
  }, [date, search, department, shiftId, status]);

  const stats = board?.stats ?? { total: 0, present: 0, late: 0, half_day: 0, absent: 0, holiday: 0, not_detected: 0 };

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Attendance board</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Employee presence and absence</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              This board shows every active employee for the selected date. Camera recognition updates check-in/check-out records, and this page refreshes automatically every 10 seconds.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadBoard()} disabled={loading}>
            Refresh
          </Button>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total employees" value={stats.total} icon={<UserRoundCheck className="h-5 w-5" />} />
        <StatCard label="Present" value={stats.present} icon={<UserRoundCheck className="h-5 w-5" />} />
        <StatCard label="Late / Half day" value={(stats.late ?? 0) + (stats.half_day ?? 0)} icon={<Clock3 className="h-5 w-5" />} />
        <StatCard label="Absent" value={stats.absent} icon={<UserRoundX className="h-5 w-5" />} />
        <StatCard label="Not detected" value={stats.not_detected} icon={<TimerReset className="h-5 w-5" />} />
      </div>

      <Card className="p-5">
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr_0.8fr_0.8fr_0.8fr]">
          <Input label="Search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name, code, email" leftIcon={<Search className="h-4 w-4" />} />
          <Input label="Date" type="date" value={date} onChange={(event) => setDate(event.target.value)} leftIcon={<CalendarDays className="h-4 w-4" />} />
          <label className="grid gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Department
            <select className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100" value={department} onChange={(event) => setDepartment(event.target.value)}>
              <option value="">All departments</option>
              {departments.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Shift
            <select className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100" value={shiftId} onChange={(event) => setShiftId(event.target.value)}>
              <option value="">All shifts</option>
              {shifts.map((shift) => <option key={shift.id} value={shift.id}>{shift.name}</option>)}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Status
            <select className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100" value={status} onChange={(event) => setStatus(event.target.value as "all" | AttendanceBoardStatus)}>
              {STATUS_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
        </div>
      </Card>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200 p-5 dark:border-white/10">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Employee attendance list</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Click any employee to see sessions and detection history.</p>
        </div>
        {loading ? (
          <div className="grid min-h-64 place-items-center text-slate-500"><Loader2 className="h-7 w-7 animate-spin" /></div>
        ) : board?.employees.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.18em] text-slate-500 dark:bg-white/5">
                <tr>
                  <th className="px-5 py-4">Employee</th>
                  <th className="px-5 py-4">Department</th>
                  <th className="px-5 py-4">Shift</th>
                  <th className="px-5 py-4">Status</th>
                  <th className="px-5 py-4">First seen</th>
                  <th className="px-5 py-4">Last seen</th>
                  <th className="px-5 py-4">Present</th>
                  <th className="px-5 py-4">Absent</th>
                  <th className="px-5 py-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-white/10">
                {board.employees.map((employee) => (
                  <tr key={employee.employee_id} className="hover:bg-slate-50/70 dark:hover:bg-white/[0.03]">
                    <td className="px-5 py-4">
                      <button className="text-left" onClick={() => setSelectedEmployee(employee)}>
                        <div className="font-semibold text-slate-900 dark:text-white">{employee.employee_name}</div>
                        <div className="text-xs text-slate-500">{employee.employee_code} · {employee.email}</div>
                      </button>
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{employee.department ?? "—"}</td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{employee.shift_name ?? "—"}</td>
                    <td className="px-5 py-4"><Badge tone={statusTone(employee.status)} className="capitalize">{statusLabel(employee.status)}</Badge></td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{formatDateTime(employee.first_seen_at)}</td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{formatDateTime(employee.last_seen_at)}</td>
                    <td className="px-5 py-4 font-medium text-slate-900 dark:text-white">{formatDuration(employee.total_present_minutes)}</td>
                    <td className="px-5 py-4 font-medium text-slate-900 dark:text-white">{formatDuration(employee.total_absent_minutes)}</td>
                    <td className="px-5 py-4">
                      <Button variant="secondary" size="sm" leftIcon={<Eye className="h-4 w-4" />} onClick={() => setSelectedEmployee(employee)}>View</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8"><EmptyState title="No employees found" description="Change filters or add active employees to view attendance." action={<X className="h-6 w-6 text-slate-400" />} /></div>
        )}
      </Card>

      <EmployeeSummaryModal employee={selectedEmployee} date={date} onClose={() => setSelectedEmployee(null)} />
      {toast ? <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} /> : null}
    </div>
  );
}
'''
write('frontend/src/pages/client-admin/attendance/AttendanceBoard.tsx', board_page)

# 5) Routes: add lazy page and route for tenant/client admins.
routes_path = 'frontend/src/routes/AppRoutes.tsx'
routes = read(routes_path)
if 'AttendanceBoardPage' not in routes:
    routes = routes.replace(
        'const LiveAttendancePage = lazy(() => import("@/pages/client-admin/attendance/LiveAttendance").then((module) => ({ default: module.LiveAttendancePage })));',
        'const LiveAttendancePage = lazy(() => import("@/pages/client-admin/attendance/LiveAttendance").then((module) => ({ default: module.LiveAttendancePage })));\nconst AttendanceBoardPage = lazy(() => import("@/pages/client-admin/attendance/AttendanceBoard").then((module) => ({ default: module.AttendanceBoardPage })));',
        1,
    )
    routes = routes.replace(
        '<Route path="/tenant-admin/attendance/live" element={<LiveAttendancePage />} />',
        '<Route path="/tenant-admin/attendance/board" element={<AttendanceBoardPage />} />\n                <Route path="/tenant-admin/attendance/live" element={<LiveAttendancePage />} />',
        1,
    )
    routes = routes.replace(
        '<Route path="/client-admin/attendance/live" element={<LiveAttendancePage />} />',
        '<Route path="/client-admin/attendance/board" element={<AttendanceBoardPage />} />\n                <Route path="/client-admin/attendance/live" element={<LiveAttendancePage />} />',
        1,
    )
    write(routes_path, routes)

# 6) Sidebar: make first attendance tab the board.
modules_path = 'frontend/src/constants/modules.ts'
modules = read(modules_path)
modules = modules.replace(
    '{ key: "tenant-attendance-live", label: "Live Attendance", path: "/client-admin/attendance/live", icon: "ScanFace" },',
    '{ key: "tenant-attendance-board", label: "Attendance Board", path: "/client-admin/attendance/board", icon: "ClipboardList" },',
)
modules = modules.replace(
    'path: "/client-admin/attendance/settings",\n  icon: "CalendarCheck2",',
    'path: "/client-admin/attendance/board",\n  icon: "CalendarCheck2",',
    1,
)
write(modules_path, modules)

print('Attendance Board update completed.')
print('Run: cd frontend && npm run build')
