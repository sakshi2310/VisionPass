import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type AttendanceWorkingDay = {
  id: string;
  tenant_id: string;
  day_of_week: number;
  is_working: boolean;
  created_at: string;
  updated_at: string;
};

export type AttendanceSettings = {
  id: string;
  tenant_id: string;
  duplicate_detection_cooldown_minutes: number;
  allow_manual_correction: boolean;
  require_correction_reason: boolean;
  timezone: string;
  created_at: string;
  updated_at: string;
};

export type AttendanceSettingsResponse = {
  attendance_settings: AttendanceSettings;
  working_days: AttendanceWorkingDay[];
};

export type AttendanceShift = {
  id: string;
  tenant_id: string;
  name: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: number;
  late_after_minutes: number;
  half_day_min_minutes: number;
  full_day_min_minutes: number;
  auto_checkout_time?: string | null;
  break_duration_minutes: number;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AttendanceHoliday = {
  id: string;
  tenant_id: string;
  holiday_name: string;
  holiday_date: string;
  department_id?: string | null;
  location_id?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AttendanceFaceSettings = {
  id: string;
  tenant_id: string;
  face_match_threshold: number;
  min_face_images: number;
  recommended_face_images: number;
  max_face_images: number;
  min_face_size_px: number;
  min_resolution_width: number;
  min_resolution_height: number;
  max_blur_score: number;
  min_brightness: number;
  max_brightness: number;
  embedding_model: string;
  embedding_version?: string | null;
  embedding_dimension: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Employee = {
  id: string;
  tenant_id: string;
  employee_code: string;
  full_name: string;
  email: string;
  mobile?: string | null;
  gender?: string | null;
  date_of_birth?: string | null;
  department?: string | null;
  designation?: string | null;
  shift_id?: string | null;
  joining_date?: string | null;
  employee_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type EmployeePortalAccount = {
  user_id: string;
  email: string;
  role: string;
  temporary_password?: string | null;
  created: boolean;
};

export type EmployeeCreateResponse = {
  employee: Employee;
  portal_account?: EmployeePortalAccount | null;
};

export type EmployeeFaceProfile = {
  id: string;
  tenant_id: string;
  employee_id: string;
  enrollment_status: "Not Enrolled" | "Processing" | "Enrolled" | "Failed" | string;
  face_count: number;
  embedding_count: number;
  average_quality_score?: number | null;
  last_enrolled_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type EmployeeFaceImage = {
  id: string;
  tenant_id: string;
  employee_id: string;
  image_url: string;
  original_filename?: string | null;
  image_type?: string | null;
  quality_score?: number | null;
  face_detected: boolean;
  face_count: number;
  validation_status: string;
  validation_message?: string | null;
  embedding_generated: boolean;
  created_at: string;
};

export type EmployeeFaceEmbedding = {
  id: string;
  tenant_id: string;
  employee_id: string;
  face_image_id?: string | null;
  embedding_model: string;
  version?: string | null;
  quality_score?: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type FaceEnrollmentSummary = {
  total_employees: number;
  enrolled_employees: number;
  in_progress_employees: number;
  failed_employees: number;
  total_images: number;
  total_embeddings: number;
};

export type AttendanceEvent = {
  id: string;
  tenant_id: string;
  employee_id: string;
  event_type: "check_in" | "check_out";
  source: "camera" | "manual" | "web";
  camera_id?: string | null;
  confidence?: number | null;
  event_time: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type DailyAttendance = {
  id: string;
  tenant_id: string;
  employee_id: string;
  attendance_date: string;
  first_check_in?: string | null;
  last_check_out?: string | null;
  total_work_minutes: number;
  status: "present" | "late" | "half_day" | "absent" | "holiday";
  shift_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type AttendanceBoardStatus = "present" | "late" | "half_day" | "absent" | "holiday" | "not_detected";

export type AttendanceLiveCameraStatus = {
  camera_id?: string | null;
  camera_name?: string | null;
  enabled: boolean;
  health_status: string;
  last_frame_at?: string | null;
};

export type AttendanceBoardEmployee = {
  employee_id: string;
  employee_code: string;
  employee_name: string;
  status: AttendanceBoardStatus;
  check_in_time?: string | null;
  check_out_time?: string | null;
  work_minutes: number;
  latest_source?: string | null;
  reason?: string | null;
  last_seen_time?: string | null;
  latest_event_time?: string | null;
  latest_event_type?: string | null;
  shift_id?: string | null;
  shift_name?: string | null;
  email?: string | null;
  department?: string | null;
  designation?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  total_present_minutes?: number;
  total_absent_minutes?: number;
  sessions_count?: number;
  latest_event_source?: string | null;
  latest_confidence?: number | null;
  attendance_message?: string | null;
};

export type AttendanceLatestSession = {
  event_id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  event_type: string;
  source?: string | null;
  event_time: string;
  camera_id?: string | null;
  camera_name?: string | null;
  confidence?: number | null;
  metadata: Record<string, unknown>;
};

export type AttendanceBoardDebugSummary = {
  tenant_id: string;
  selected_date: string;
  total_active_employees: number;
  present_count: number;
  absent_count: number;
  not_detected_count: number;
  holiday_count: number;
  latest_event_time?: string | null;
  active_attendance_camera_count: number;
  camera_enabled: boolean;
  last_camera_frame_time?: string | null;
  last_recognition_result?: string | null;
  unknown_face_count: number;
  no_face_count: number;
};

export type AttendanceBoardResponse = {
  attendance_date: string;
  generated_at: string;
  present_employees: AttendanceBoardEmployee[];
  absent_employees: AttendanceBoardEmployee[];
  latest_sessions: AttendanceLatestSession[];
  debug_summary: AttendanceBoardDebugSummary;
  employees?: AttendanceBoardEmployee[];
  stats?: Record<string, number>;
  live_camera_status?: AttendanceLiveCameraStatus | null;
};

export type AttendanceSession = {
  check_in: string;
  check_out?: string | null;
  duration_minutes: number;
  source?: string | null;
  camera_id?: string | null;
  confidence?: number | null;
  is_open: boolean;
  session_type?: "present" | "absent";
  reason?: string | null;
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

export type AttendanceMarkResponse = {
  event: AttendanceEvent;
  daily: DailyAttendance;
  employee_id: string;
  employee_name: string;
  employee_code: string;
  message: string;
};

export type RecognitionResult = {
  recognized: boolean;
  employee_id?: string | null;
  employee_name?: string | null;
  confidence?: number | null;
  distance?: number | null;
  threshold: number;
  recognition_status: "MATCHED" | "UNKNOWN" | "LOW_CONFIDENCE" | "NO_FACE" | "MULTIPLE_FACES";
};

export type CameraDetectionZone = {
  id: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
};

export type Camera = {
  id: string;
  tenant_id: string;
  name: string;
  location: string;
  camera_type: "ip_webcam" | "phone_ip_webcam" | "rtsp" | "http_mjpeg" | "webcam" | "manual" | "manual_snapshot";
  phone_ip?: string | null;
  port?: number | null;
  stream_url?: string | null;
  snapshot_url?: string | null;
  assigned_feature_scope: "attendance" | "object_detection" | "both";
  detection_zones: CameraDetectionZone[];
  username?: string | null;
  has_credentials: boolean;
  is_active: boolean;
  health_status: "online" | "offline" | "error" | "unknown";
  last_seen_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type CameraPayload = {
  name: string;
  location: string;
  camera_type: Camera["camera_type"];
  phone_ip?: string | null;
  port?: number | null;
  stream_url?: string | null;
  snapshot_url?: string | null;
  assigned_feature_scope: Camera["assigned_feature_scope"];
  detection_zones?: CameraDetectionZone[];
  username?: string | null;
  password?: string | null;
  clear_password?: boolean;
  is_active: boolean;
};

export type CameraTestResult = {
  camera_id: string;
  success: boolean;
  health_status: Camera["health_status"];
  message: string;
  width?: number | null;
  height?: number | null;
  content_type?: string | null;
};

export type CameraEvent = {
  id: string;
  tenant_id: string;
  camera_id: string;
  event_type: string;
  employee_id?: string | null;
  recognition_status: string;
  confidence?: number | null;
  image_path?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type CameraFrameResult = {
  camera: Camera;
  camera_event: CameraEvent;
  frame: {
    width: number;
    height: number;
    content_type: string;
    frame_interval_seconds: number;
    request_timeout_seconds: number;
  };
  recognition?: RecognitionResult | null;
  attendance?: AttendanceMarkResponse | null;
};

export type EmployeePayload = {
  employee_code?: string;
  full_name: string;
  email: string;
  mobile?: string | null;
  gender?: string | null;
  date_of_birth?: string | null;
  department?: string | null;
  designation?: string | null;
  shift_id?: string | null;
  joining_date?: string | null;
  employee_type: string;
  is_active: boolean;
};

export type EmployeeUpdatePayload = Partial<EmployeePayload>;

export type FaceImageValidationResult = {
  filename?: string | null;
  status: "Validated" | "Failed" | string;
  enrollment_status: "valid" | "rejected" | "pending" | string;
  code?: string | null;
  message: string;
  detection_confidence?: number | null;
  quality_score?: number | null;
  width?: number | null;
  height?: number | null;
  face_count?: number | null;
  face_size_px?: number | null;
  blur_score?: number | null;
  brightness?: number | null;
  duplicate_employee_id?: string | null;
  duplicate_employee_name?: string | null;
  duplicate_distance?: number | null;
  duplicate_similarity?: number | null;
};

export type FaceEnrollmentPayload = {
  files: File[];
  re_enroll?: boolean;
};

export type FaceSettingsPayload = {
  face_match_threshold: number;
  min_face_images: number;
  recommended_face_images: number;
  max_face_images: number;
  min_face_size_px: number;
  min_resolution_width: number;
  min_resolution_height: number;
  max_blur_score: number;
  min_brightness: number;
  max_brightness: number;
  embedding_model: string;
  embedding_version?: string | null;
  embedding_dimension: number;
  is_active: boolean;
};

type AttendanceShiftListResponse = { shifts: AttendanceShift[] };
type AttendanceHolidayListResponse = { holidays: AttendanceHoliday[] };
export type EmployeeListResponse = { employees: Employee[] };
export type EmployeeFaceImageListResponse = { images: EmployeeFaceImage[] };
export type EmployeeFaceEmbeddingListResponse = { embeddings: EmployeeFaceEmbedding[] };
export type EmployeeFaceEnrollmentResponse = {
  profile: EmployeeFaceProfile;
  images: EmployeeFaceImage[];
  embeddings: EmployeeFaceEmbedding[];
  validation_results: FaceImageValidationResult[];
};

type AttendanceSettingsPayload = {
  duplicate_detection_cooldown_minutes: number;
  allow_manual_correction: boolean;
  require_correction_reason: boolean;
  timezone: string;
  working_days: number[];
};

export type AttendanceShiftPayload = {
  name: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: number;
  late_after_minutes: number;
  half_day_min_minutes: number;
  full_day_min_minutes: number;
  auto_checkout_time?: string | null;
  break_duration_minutes: number;
  is_default: boolean;
  is_active: boolean;
};

export type AttendanceShiftUpdatePayload = Partial<AttendanceShiftPayload>;

export type AttendanceHolidayPayload = {
  holiday_name: string;
  holiday_date: string;
  department_id?: string | null;
  location_id?: string | null;
  is_active: boolean;
};

export type AttendanceHolidayUpdatePayload = Partial<AttendanceHolidayPayload>;

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (!API_BASE) return normalizedPath;
  if (API_BASE.endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return `${API_BASE}${normalizedPath.slice(4)}`;
  }
  return `${API_BASE}${normalizedPath}`;
}

function authHeaders() {
  const token = loadStoredAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Request failed.";
    let code: string | undefined;
    let validationResults: FaceImageValidationResult[] = [];
    try {
      const payload = (await response.json()) as {
        detail?: string | {
          code?: string;
          message?: string;
          validation_results?: FaceImageValidationResult[];
        };
        message?: string;
      };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (payload.detail) {
        message = payload.detail.message ?? message;
        code = payload.detail.code;
        validationResults = payload.detail.validation_results ?? [];
      } else {
        message = payload.message ?? message;
      }
    } catch {
      // keep default message
    }
    throw new FaceEnrollmentApiError(message, code, validationResults);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export class FaceEnrollmentApiError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
    public readonly validationResults: FaceImageValidationResult[] = [],
  ) {
    super(message);
    this.name = "FaceEnrollmentApiError";
  }
}

function faceEnrollmentForm(payload: FaceEnrollmentPayload): FormData {
  const form = new FormData();
  payload.files.forEach((file) => form.append("files", file, file.name));
  form.append("re_enroll", String(payload.re_enroll ?? false));
  return form;
}

export async function fetchAttendanceSettings(): Promise<AttendanceSettingsResponse> {
  return requestJson<AttendanceSettingsResponse>("/api/client-admin/attendance/settings");
}

export async function updateAttendanceSettings(payload: AttendanceSettingsPayload): Promise<AttendanceSettingsResponse> {
  return requestJson<AttendanceSettingsResponse>("/api/client-admin/attendance/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function fetchShifts(): Promise<AttendanceShift[]> {
  const response = await requestJson<AttendanceShiftListResponse>("/api/client-admin/attendance/shifts");
  return response.shifts;
}

export function createShift(payload: AttendanceShiftPayload) {
  return requestJson<AttendanceShift>("/api/client-admin/attendance/shifts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateShift(shiftId: string, payload: AttendanceShiftUpdatePayload) {
  return requestJson<AttendanceShift>(`/api/client-admin/attendance/shifts/${shiftId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteShift(shiftId: string) {
  return requestJson<void>(`/api/client-admin/attendance/shifts/${shiftId}`, {
    method: "DELETE",
  });
}

export function setDefaultShift(shiftId: string) {
  return requestJson<AttendanceShift>(`/api/client-admin/attendance/shifts/${shiftId}/default`, {
    method: "PATCH",
  });
}

export async function fetchHolidays(): Promise<AttendanceHoliday[]> {
  const response = await requestJson<AttendanceHolidayListResponse>("/api/client-admin/attendance/holidays");
  return response.holidays;
}

export function createHoliday(payload: AttendanceHolidayPayload) {
  return requestJson<AttendanceHoliday>("/api/client-admin/attendance/holidays", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateHoliday(holidayId: string, payload: AttendanceHolidayUpdatePayload) {
  return requestJson<AttendanceHoliday>(`/api/client-admin/attendance/holidays/${holidayId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteHoliday(holidayId: string) {
  return requestJson<void>(`/api/client-admin/attendance/holidays/${holidayId}`, {
    method: "DELETE",
  });
}

export async function fetchEmployees(params?: { search?: string; department?: string; shiftId?: string; faceStatus?: string }): Promise<Employee[]> {
  const query = new URLSearchParams();
  if (params?.search) query.set("search", params.search);
  if (params?.department) query.set("department", params.department);
  if (params?.shiftId) query.set("shift_id", params.shiftId);
  if (params?.faceStatus) query.set("face_status", params.faceStatus);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await requestJson<EmployeeListResponse>(`/api/client-admin/attendance/employees${suffix}`);
  return response.employees;
}

export function createEmployee(payload: EmployeePayload) {
  return requestJson<EmployeeCreateResponse>("/api/client-admin/attendance/employees", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateEmployee(employeeId: string, payload: EmployeeUpdatePayload) {
  return requestJson<EmployeeCreateResponse>(`/api/client-admin/attendance/employees/${employeeId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function fetchEmployeeDetails(employeeId: string) {
  return requestJson<Employee>(`/api/client-admin/attendance/employees/${employeeId}`);
}

export function activateEmployee(employeeId: string) {
  return requestJson<Employee>(`/api/client-admin/attendance/employees/${employeeId}/activate`, {
    method: "PATCH",
  });
}

export function deactivateEmployee(employeeId: string) {
  return requestJson<Employee>(`/api/client-admin/attendance/employees/${employeeId}/deactivate`, {
    method: "PATCH",
  });
}

export function deleteEmployee(employeeId: string) {
  return requestJson<void>(`/api/client-admin/attendance/employees/${employeeId}`, {
    method: "DELETE",
  });
}

export function fetchFaceEnrollmentSummary() {
  return requestJson<FaceEnrollmentSummary>("/api/client-admin/attendance/face-enrollment/summary");
}

export function fetchEmployeeFaceProfile(employeeId: string) {
  return requestJson<EmployeeFaceProfile>(`/api/client-admin/attendance/employees/${employeeId}/face-profile`);
}

export function fetchEmployeeFaceImages(employeeId: string) {
  return requestJson<EmployeeFaceImageListResponse>(`/api/client-admin/attendance/employees/${employeeId}/face-images`);
}

export function fetchEmployeeFaceEmbeddings(employeeId: string) {
  return requestJson<EmployeeFaceEmbeddingListResponse>(`/api/client-admin/attendance/employees/${employeeId}/face-embeddings`);
}

export function uploadFaceImages(employeeId: string, payload: FaceEnrollmentPayload) {
  return requestJson<EmployeeFaceEnrollmentResponse>(`/api/client-admin/attendance/employees/${employeeId}/face-images`, {
    method: "POST",
    body: faceEnrollmentForm(payload),
  });
}

export function generateFaceEmbeddings(employeeId: string, payload: FaceEnrollmentPayload) {
  return requestJson<EmployeeFaceEnrollmentResponse>(`/api/client-admin/attendance/employees/${employeeId}/generate-embeddings`, {
    method: "POST",
    body: faceEnrollmentForm(payload),
  });
}

export function reEnrollFace(employeeId: string, payload: FaceEnrollmentPayload) {
  return requestJson<EmployeeFaceEnrollmentResponse>(`/api/client-admin/attendance/employees/${employeeId}/re-enroll-face`, {
    method: "POST",
    body: faceEnrollmentForm(payload),
  });
}

export function deleteFaceEnrollment(employeeId: string) {
  return requestJson<void>(`/api/client-admin/attendance/employees/${employeeId}/face-enrollment`, {
    method: "DELETE",
  });
}


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

export function markCheckIn(employeeId: string) {
  return requestJson<AttendanceMarkResponse>("/api/attendance/check-in", {
    method: "POST",
    body: JSON.stringify({ employee_id: employeeId, source: "web" }),
  });
}

export function markCheckOut(employeeId: string) {
  return requestJson<AttendanceMarkResponse>("/api/attendance/check-out", {
    method: "POST",
    body: JSON.stringify({ employee_id: employeeId, source: "web" }),
  });
}

export async function fetchCameras(): Promise<Camera[]> {
  const response = await requestJson<{ cameras: Camera[] }>("/api/cameras");
  return response.cameras;
}

export function createCamera(payload: CameraPayload) {
  return requestJson<Camera>("/api/cameras", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCamera(cameraId: string, payload: Partial<CameraPayload>) {
  return requestJson<Camera>(`/api/cameras/${cameraId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteCamera(cameraId: string) {
  return requestJson<void>(`/api/cameras/${cameraId}`, { method: "DELETE" });
}

export function testCamera(cameraId: string) {
  return requestJson<CameraTestResult>(`/api/cameras/${cameraId}/test`, {
    method: "POST",
  });
}

export async function fetchCameraSnapshot(cameraId: string): Promise<Blob> {
  const response = await fetch(buildApiUrl(`/api/cameras/${cameraId}/snapshot`), {
    method: "POST",
    headers: authHeaders(),
  });
  if (!response.ok) {
    let message = "Unable to fetch camera snapshot.";
    let code: string | undefined;
    try {
      const payload = await response.json() as { detail?: string | { code?: string; message?: string } };
      if (typeof payload.detail === "string") message = payload.detail;
      else if (payload.detail) {
        message = payload.detail.message ?? message;
        code = payload.detail.code;
      }
    } catch {
      // Keep the default message for non-JSON failures.
    }
    throw new FaceEnrollmentApiError(message, code);
  }
  return response.blob();
}

export function processCameraFrame(cameraId: string) {
  return requestJson<CameraFrameResult>(`/api/cameras/${cameraId}/process-frame`, {
    method: "POST",
  });
}

export function recognizeCameraFrame(cameraId: string) {
  return requestJson<CameraFrameResult>(`/api/cameras/${cameraId}/recognize-frame`, {
    method: "POST",
  });
}

export function recognizeAndMarkCameraAttendance(cameraId: string) {
  return requestJson<CameraFrameResult>(`/api/cameras/${cameraId}/recognize-and-mark-attendance`, {
    method: "POST",
  });
}

