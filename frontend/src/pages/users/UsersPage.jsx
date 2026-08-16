import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge, Badge } from "../../components/common/Badge";
import { userApi, departmentApi, sectionApi } from "../../services/api/entities";
import { useAuth } from "../../context/AuthContext";
import { ROLES, ROLE_LABELS } from "../../constants";
import { formatDateTime } from "../../utils";

const departmentOptionsSource = { queryKey: ["departments", "lookup"], fetcher: () => departmentApi.lookup() };
const sectionOptionsSource = {
  queryKey: ["sections", "lookup-for-users"],
  fetcher: () => sectionApi.list({ limit: 200 }),
  labelKey: "display_name",
};

const phoneSchema = z
  .string()
  .optional()
  .refine((v) => !v || /^\+?[0-9\s\-()]{7,20}$/.test(v), "Enter a valid phone number");

function roleOptionsFor(currentUserRole) {
  if (currentUserRole === ROLES.SUPER_ADMIN) {
    return Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }));
  }
  // HODs may only create Faculty/Student accounts, per backend RBAC.
  return [
    { value: ROLES.FACULTY, label: ROLE_LABELS[ROLES.FACULTY] },
    { value: ROLES.STUDENT, label: ROLE_LABELS[ROLES.STUDENT] },
  ];
}

const schema = z.object({
  name: z.string().min(2, "Name is required").max(150),
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "At least 8 characters")
    .regex(/[A-Za-z]/, "Must include a letter")
    .regex(/[0-9]/, "Must include a number"),
  role: z.enum(["super_admin", "hod", "faculty", "student"]),
  department_id: z.string().optional().or(z.literal("")),
  section_id: z.string().optional().or(z.literal("")),
  phone: phoneSchema,
});

const updateSchema = z.object({
  name: z.string().min(2).max(150).optional(),
  role: z.enum(["super_admin", "hod", "faculty", "student"]).optional(),
  department_id: z.string().optional().or(z.literal("")),
  section_id: z.string().optional().or(z.literal("")),
  phone: phoneSchema,
});

const columns = [
  { header: "Name", accessorKey: "name", sortKey: "name" },
  { header: "Email", accessorKey: "email", sortKey: "email" },
  { header: "Role", accessorFn: (row) => row, cell: (info) => <Badge variant="brand">{ROLE_LABELS[info.getValue().role]}</Badge> },
  { header: "Department", accessorFn: (row) => row.department?.name ?? "—" },
  { header: "Last login", accessorFn: (row) => formatDateTime(row.last_login) },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function UsersPage() {
  const { user } = useAuth();
  const roleOptions = roleOptionsFor(user?.role);

  const fields = [
    { name: "name", label: "Full name", type: "text", required: true },
    { name: "email", label: "Email", type: "email", required: true },
    { name: "password", label: "Password", type: "password", required: true, hint: "At least 8 characters, with a letter and a number" },
    { name: "role", label: "Role", type: "select", required: true, options: roleOptions },
    {
      name: "department_id",
      label: "Department",
      type: "select",
      optionsSource: departmentOptionsSource,
      hint: "Required for HOD, Faculty and Student roles",
    },
    {
      name: "section_id",
      label: "Section",
      type: "select",
      optionsSource: sectionOptionsSource,
      hint: "Students only - which section they belong to",
    },
    { name: "phone", label: "Phone", type: "text" },
  ];

  const editFields = [fields[0], { ...fields[1], disabled: true, hint: "Email can't be changed" }, fields[3], fields[4], fields[5], fields[6]];

  return (
    <EntityListPage
      title="Users"
      subtitle="Login accounts and role assignment."
      queryKey="users"
      api={userApi}
      entityLabel="User"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by name or email…"
      transformSubmit={(data) => ({
        ...data,
        department_id: data.department_id || null,
        section_id: data.section_id || null,
      })}
      getDefaultValues={(row) => ({
        name: row.name,
        email: row.email,
        role: row.role,
        department_id: row.department?.id ?? "",
        section_id: row.section?.id ?? "",
        phone: row.phone ?? "",
      })}
    />
  );
}
