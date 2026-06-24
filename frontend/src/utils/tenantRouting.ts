function toSlugSegment(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/["']/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function buildTenantLoginPath(organizationName: string) {
  const slug = toSlugSegment(organizationName);
  return slug ? `/login?org=${encodeURIComponent(slug)}` : "/login";
}

export function formatTenantLabel(value: string) {
  const text = value.trim().replace(/[-_]+/g, " ");
  if (!text) return "";
  return text
    .split(/\s+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
