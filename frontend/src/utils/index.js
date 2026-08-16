/**
 * Joins conditional class names together, skipping falsy values.
 * A tiny hand-rolled equivalent of `clsx`/`classnames` so we don't add
 * another dependency for something this small.
 * @param {...(string|false|null|undefined)} classes
 * @returns {string}
 */
export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

/**
 * @param {string|Date|null|undefined} value
 * @returns {string}
 */
export function formatDate(value) {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

/**
 * @param {string|Date|null|undefined} value
 * @returns {string}
 */
export function formatDateTime(value) {
  if (!value) return "—";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/**
 * Formats a 24-hour "HH:MM" string as a friendlier 12-hour label, e.g.
 * "09:00" -> "9:00 AM". Falls back to the raw value if parsing fails.
 * @param {string} hhmm
 * @returns {string}
 */
export function formatTime(hhmm) {
  if (!hhmm || !hhmm.includes(":")) return hhmm ?? "—";
  const [hours, minutes] = hhmm.split(":").map(Number);
  const period = hours >= 12 ? "PM" : "AM";
  const twelveHour = hours % 12 === 0 ? 12 : hours % 12;
  return `${twelveHour}:${String(minutes).padStart(2, "0")} ${period}`;
}

/**
 * Extracts a human-readable message from an Axios error, falling back
 * gracefully if the backend's standard envelope isn't present (e.g. a
 * network failure that never reached the server).
 * @param {unknown} error
 * @param {string} fallback
 * @returns {string}
 */
export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const data = error?.response?.data;
  if (data?.errors?.length) {
    return data.errors.map((e) => (e.field ? `${e.field}: ${e.message}` : e.message)).join(" ");
  }
  if (data?.message) return data.message;
  if (error?.message === "Network Error") return "Couldn't reach the server. Check your connection and try again.";
  return fallback;
}

/**
 * @param {string} name
 * @returns {string} up to 2 uppercase initials, for avatar placeholders
 */
export function getInitials(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  const initials = parts.length === 1 ? parts[0].slice(0, 2) : parts[0][0] + parts[parts.length - 1][0];
  return initials.toUpperCase();
}
