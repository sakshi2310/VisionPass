import type {
  AccessRecord,
  AlertItem,
  AttendanceRecord,
  ChatMessage,
  FeatureRule,
  Tenant,
  VisitorRecord,
} from "@/types";
import { moduleDefinitions } from "@/constants/modules";

export const tenants: Tenant[] = [
  {
    id: "tenant-northern",
    name: "Northern Lights HQ",
    code: "NL-HQ",
    plan: "Enterprise",
    industry: "Corporate",
    status: "active",
    enabledModules: [
      "attendance",
      "visitor_classification",
      "access_control",
      "alerts",
      "genai_assistant",
      "analytics",
    ],
    users: 248,
    sites: 6,
    alertsToday: 14,
    cameras: 38,
  },
  {
    id: "tenant-archon",
    name: "Archon Industrial",
    code: "ARC-02",
    plan: "Enterprise Plus",
    industry: "Manufacturing",
    status: "active",
    enabledModules: [
      "attendance",
      "visitor_classification",
      "access_control",
      "alerts",
      "anomaly_detection",
      "genai_assistant",
      "analytics",
    ],
    users: 615,
    sites: 9,
    alertsToday: 27,
    cameras: 112,
  },
  {
    id: "tenant-sunrise",
    name: "Sunrise Health",
    code: "SRH-11",
    plan: "Growth",
    industry: "Healthcare",
    status: "trial",
    enabledModules: ["attendance", "alerts", "analytics"],
    users: 83,
    sites: 2,
    alertsToday: 6,
    cameras: 21,
  },
];

export const attendanceRows: AttendanceRecord[] = [
  {
    id: "att-1",
    employee: "Arjun Mehta",
    time: "08:07 AM",
    status: "checked_in",
    confidence: 98,
    camera: "Lobby Camera 01",
    action: "Auto-approved",
    date: "2026-06-21",
  },
  {
    id: "att-2",
    employee: "Priya Sharma",
    time: "08:13 AM",
    status: "late",
    confidence: 91,
    camera: "Gate A Camera",
    action: "Late threshold warning",
    date: "2026-06-21",
  },
  {
    id: "att-3",
    employee: "Daniel Brooks",
    time: "09:02 AM",
    status: "manual",
    confidence: 87,
    camera: "Side Entrance",
    action: "Manual review",
    date: "2026-06-21",
  },
  {
    id: "att-4",
    employee: "Nina Rao",
    time: "07:58 AM",
    status: "checked_in",
    confidence: 99,
    camera: "Lobby Camera 02",
    action: "Auto-approved",
    date: "2026-06-20",
  },
  {
    id: "att-5",
    employee: "Omar Hassan",
    time: "08:36 AM",
    status: "absent",
    confidence: 76,
    camera: "N/A",
    action: "No face match",
    date: "2026-06-20",
  },
];

export const visitorLogs: VisitorRecord[] = [
  {
    id: "vis-1",
    name: "Unknown visitor #184",
    classification: "unknown",
    confidence: 83,
    firstSeen: "06:15 PM",
    lastSeen: "06:32 PM",
    camera: "Front Gate",
    thumbnail: "UV",
  },
  {
    id: "vis-2",
    name: "Rachel Green",
    classification: "vendor",
    confidence: 95,
    firstSeen: "02:12 PM",
    lastSeen: "02:24 PM",
    camera: "Loading Bay",
    thumbnail: "RG",
  },
  {
    id: "vis-3",
    name: "Unknown visitor #219",
    classification: "unknown",
    confidence: 74,
    firstSeen: "08:06 PM",
    lastSeen: "08:15 PM",
    camera: "Side Door",
    thumbnail: "UV",
  },
];

export const accessEvents: AccessRecord[] = [
  {
    id: "acc-1",
    identity: "Arjun Mehta",
    status: "allowed",
    gate: "North Gate",
    reason: "Valid badge, within shift window",
    timestamp: "08:08 AM",
    confidence: 98,
  },
  {
    id: "acc-2",
    identity: "Unknown visitor #184",
    status: "denied",
    gate: "Server Room",
    reason: "No clearance for restricted zone",
    timestamp: "06:18 PM",
    confidence: 83,
  },
  {
    id: "acc-3",
    identity: "Priya Sharma",
    status: "allowed",
    gate: "Reception turnstile",
    reason: "Manual override approved",
    timestamp: "08:17 AM",
    confidence: 92,
  },
];

export const alerts: AlertItem[] = [
  {
    id: "al-1",
    title: "Unknown person detected after hours",
    severity: "critical",
    category: "Visitor",
    time: "06:54 PM",
    detail: "A person without a match appeared near the rear entrance after the premises were closed.",
    resolved: false,
  },
  {
    id: "al-2",
    title: "Possible tailgating at Gate B",
    severity: "high",
    category: "Access",
    time: "05:21 PM",
    detail: "Two people passed through a single access decision within 3 seconds.",
    resolved: false,
  },
  {
    id: "al-3",
    title: "Lobby crowding anomaly",
    severity: "medium",
    category: "Anomaly",
    time: "12:40 PM",
    detail: "Foot traffic rose 38% above the baseline during lunch.",
    resolved: true,
  },
  {
    id: "al-4",
    title: "Late check-in pattern",
    severity: "low",
    category: "Attendance",
    time: "09:15 AM",
    detail: "Three employees checked in after the office grace period.",
    resolved: true,
  },
];

export const chatSeed: ChatMessage[] = [
  {
    id: "msg-1",
    role: "assistant",
    content:
      "I can help you query attendance, visitors, access decisions, and alerts across the selected tenant.",
    time: "Just now",
  },
];

export const dashboardStats = [
  { label: "Today Check-ins", value: "184", delta: "+12% vs yesterday", tone: "brand" as const },
  { label: "Unknown Visitors", value: "17", delta: "-4 from yesterday", tone: "amber" as const },
  { label: "Active Alerts", value: "6", delta: "2 critical", tone: "rose" as const },
  { label: "Access Decisions", value: "1,204", delta: "99.2% approved", tone: "emerald" as const },
];

export const attendanceTrend = [
  { name: "Mon", checkedIn: 176, late: 8 },
  { name: "Tue", checkedIn: 182, late: 7 },
  { name: "Wed", checkedIn: 190, late: 6 },
  { name: "Thu", checkedIn: 178, late: 9 },
  { name: "Fri", checkedIn: 194, late: 5 },
  { name: "Sat", checkedIn: 121, late: 2 },
  { name: "Sun", checkedIn: 97, late: 1 },
];

export const analyticsSeries = {
  attendance: [
    { name: "W1", value: 420 },
    { name: "W2", value: 448 },
    { name: "W3", value: 462 },
    { name: "W4", value: 481 },
  ],
  unknownVisitors: [
    { name: "W1", value: 14 },
    { name: "W2", value: 19 },
    { name: "W3", value: 11 },
    { name: "W4", value: 17 },
  ],
  alertSeverity: [
    { name: "Low", value: 16 },
    { name: "Medium", value: 9 },
    { name: "High", value: 5 },
    { name: "Critical", value: 3 },
  ],
  moduleUsage: moduleDefinitions.map((module, index) => ({
    name: module.label,
    value: 58 - index * 5,
  })),
};

export const systemUsage = [
  { name: "Tenant APIs", value: 78 },
  { name: "Model Inference", value: 63 },
  { name: "Audit Queue", value: 42 },
  { name: "Camera Events", value: 87 },
];

export const featureRules: FeatureRule[] = [
  {
    id: "rule-object-detection",
    name: "Object detection review",
    description: "Escalate when the camera sees an unattended object near entrances or restricted zones.",
    category: "Object detection",
    tenantScope: "All tenants",
    status: "active",
    enabled: true,
    threshold: 82,
    action: "Create critical alert and notify security",
    createdAt: "2026-06-12",
    updatedAt: "2026-06-20",
  },
  {
    id: "rule-after-hours",
    name: "After-hours movement",
    description: "Flag any person entering after site close unless they have supervisor override.",
    category: "After-hours access",
    tenantScope: "Northern Lights HQ",
    status: "active",
    enabled: true,
    threshold: 90,
    action: "Alert guard desk and create log entry",
    createdAt: "2026-06-11",
    updatedAt: "2026-06-19",
  },
  {
    id: "rule-tailgating",
    name: "Tailgating watch",
    description: "Detect multiple bodies passing through a gate on a single approved credential.",
    category: "Access anomaly",
    tenantScope: "Archon Industrial",
    status: "paused",
    enabled: false,
    threshold: 77,
    action: "Queue for human review",
    createdAt: "2026-06-09",
    updatedAt: "2026-06-18",
  },
];
