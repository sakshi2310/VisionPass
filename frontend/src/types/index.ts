export type Role =
  | "SUPER_ADMIN"
  | "TENANT_ADMIN"
  | "TENANT_USER"
  | "SECURITY_GUARD"
  | "RECEPTIONIST"
  | "ATTENDANCE_OPERATOR"
  | "CAMERA_OPERATOR"
  | "MANAGER"
  | "CLIENT_ADMIN"
  | "CLIENT_USER";
export type ThemeMode = "dark" | "light";

export type ModuleKey =
  | "attendance"
  | "visitor_classification"
  | "visitor_management"
  | "face_recognition"
  | "anpr"
  | "ppe_detection"
  | "crowd_detection"
  | "object_detection"
  | "emotion_analytics"
  | "intrusion_detection"
  | "live_feed"
  | "reports"
  | "access_control"
  | "alerts"
  | "anomaly_detection"
  | "genai_assistant"
  | "analytics"
  | "camera_management";

export type Severity = "low" | "medium" | "high" | "critical";
export type DecisionStatus = "allowed" | "denied";
export type AttendanceStatus = "checked_in" | "late" | "absent" | "manual";
export type RuleStatus = "active" | "paused" | "draft";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  tenantId: string;
  title?: string;
  avatar?: string;
  phone?: string;
  department?: string;
  designation?: string;
  employeeId?: string;
  accessZones?: string[];
  faceEnrolled?: boolean;
  isActive?: boolean;
  isDeleted?: boolean;
  notes?: string;
  lastLoginAt?: string | null;
  createdBy?: string | null;
}

export interface Tenant {
  id: string;
  name: string;
  code: string;
  plan: string;
  industry: string;
  status: "active" | "inactive" | "suspended" | "trial" | "paused";
  enabledModules: string[];
  logo_url?: string;
  address?: string;
  users: number;
  sites: number;
  alertsToday: number;
  cameras: number;
  maxUsers?: number;
  maxDevices?: number;
  adminName?: string;
  adminEmail?: string;
  phone?: string;
  featuresCount?: number;
  created_at?: string;
  updated_at?: string;
}

export interface AttendanceRecord {
  id: string;
  employee: string;
  time: string;
  status: AttendanceStatus;
  confidence: number;
  camera: string;
  action: string;
  date: string;
}

export interface VisitorRecord {
  id: string;
  name: string;
  classification: "unknown" | "staff" | "vendor";
  confidence: number;
  firstSeen: string;
  lastSeen: string;
  camera: string;
  thumbnail: string;
}

export interface AccessRecord {
  id: string;
  identity: string;
  status: DecisionStatus;
  gate: string;
  reason: string;
  timestamp: string;
  confidence: number;
}

export interface AlertItem {
  id: string;
  title: string;
  severity: Severity;
  category: string;
  time: string;
  detail: string;
  resolved: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  time: string;
}

export interface NavItem {
  key: string;
  label: string;
  path: string;
  icon: string;
  moduleKey?: ModuleKey;
  adminOnly?: boolean;
  children?: NavItem[];
}

export interface ModuleDefinition {
  key: ModuleKey;
  label: string;
  description: string;
  route: string;
  icon: string;
}

export interface StatDefinition {
  label: string;
  value: string;
  delta: string;
  tone: "brand" | "emerald" | "amber" | "rose";
}

export interface FeatureRule {
  id: string;
  name: string;
  description: string;
  category: string;
  tenantScope: string;
  status: RuleStatus;
  enabled: boolean;
  threshold: number;
  action: string;
  createdAt: string;
  updatedAt: string;
}
