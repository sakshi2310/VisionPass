import type { ModuleKey } from "@/types";

export const FEATURE_KEYS = {
  attendance: "attendance",
  visitorUnknown: "visitor_unknown",
  objectDetection: "object_detection",
} as const satisfies Record<string, ModuleKey>;

export const featureRegistry = {
  common: {
    label: "Common",
    features: ["dashboard", "cameras", "phone_ip_webcam", "live_feed", "reports_overview", "members", "settings"],
  },
  attendance: {
    label: "Attendance",
    moduleKey: FEATURE_KEYS.attendance,
    features: [
      "attendance_dashboard",
      "employees",
      "face_enrollment",
      "shifts",
      "holidays",
      "attendance_config",
      "attendance_live",
      "attendance_logs",
      "attendance_reports",
    ],
  },
  visitorUnknown: {
    label: "Visitor + Unknown",
    moduleKey: FEATURE_KEYS.visitorUnknown,
    features: [
      "person_detection",
      "visitors",
      "unknown_review",
      "visitor_reports",
    ],
  },
  objectDetection: {
    label: "Object Detection",
    moduleKey: FEATURE_KEYS.objectDetection,
    features: [
      "object_detection_dashboard",
      "detection_models",
      "detection_rules",
      "detection_live",
      "detection_events",
      "detection_alerts",
      "detection_reports",
      "detection_zones",
    ],
  },
} as const;

export function hasTenantProductFeature(enabledModules: string[], key: ModuleKey) {
  return enabledModules.includes(key);
}
