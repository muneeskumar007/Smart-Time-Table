// Mirrors backend/app/core/constants.py::UserRole - keep these two files
// in sync if roles ever change.
export const ROLES = {
  SUPER_ADMIN: "super_admin",
  HOD: "hod",
  FACULTY: "faculty",
  STUDENT: "student",
};

export const ROLE_LABELS = {
  [ROLES.SUPER_ADMIN]: "Super Admin",
  [ROLES.HOD]: "Department Admin (HOD)",
  [ROLES.FACULTY]: "Faculty",
  [ROLES.STUDENT]: "Student",
};

export const MANAGER_ROLES = [ROLES.SUPER_ADMIN, ROLES.HOD];

/**
 * @typedef {Object} NavItem
 * @property {string} label
 * @property {string} path
 * @property {string} icon - lucide-react icon name
 * @property {string[]} roles - which roles see this item
 */

/** @type {NavItem[]} */
export const NAV_ITEMS = [
  { label: "Dashboard", path: "/dashboard", icon: "LayoutDashboard", roles: [ROLES.SUPER_ADMIN, ROLES.HOD, ROLES.FACULTY, ROLES.STUDENT] },
  { label: "Departments", path: "/departments", icon: "Building2", roles: [ROLES.SUPER_ADMIN] },
  { label: "Users", path: "/users", icon: "Users", roles: [ROLES.SUPER_ADMIN, ROLES.HOD] },
  { label: "Faculty", path: "/faculty", icon: "GraduationCap", roles: [ROLES.SUPER_ADMIN, ROLES.HOD] },
  { label: "Courses", path: "/courses", icon: "BookOpen", roles: [ROLES.SUPER_ADMIN, ROLES.HOD] },
  { label: "Subjects", path: "/subjects", icon: "Notebook", roles: [ROLES.SUPER_ADMIN, ROLES.HOD] },
  { label: "Sections", path: "/sections", icon: "Layers", roles: [ROLES.SUPER_ADMIN, ROLES.HOD] },
  { label: "Rooms", path: "/rooms", icon: "DoorOpen", roles: [ROLES.SUPER_ADMIN] },
  { label: "Academic Years", path: "/academic-years", icon: "CalendarRange", roles: [ROLES.SUPER_ADMIN] },
  { label: "Semesters", path: "/semesters", icon: "CalendarClock", roles: [ROLES.SUPER_ADMIN] },
  { label: "Time Slots", path: "/timeslots", icon: "Clock", roles: [ROLES.SUPER_ADMIN, ROLES.HOD] },
];

export const DEFAULT_PAGE_SIZE = 10;
export const PAGE_SIZE_OPTIONS = [10, 25, 50];
