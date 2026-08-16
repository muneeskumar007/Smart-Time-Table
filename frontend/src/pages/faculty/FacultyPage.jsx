import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge } from "../../components/common/Badge";
import { facultyApi, departmentApi } from "../../services/api/entities";
import { formatDate } from "../../utils";

const departmentOptionsSource = { queryKey: ["departments", "lookup"], fetcher: () => departmentApi.lookup() };

const EMPLOYMENT_TYPE_OPTIONS = [
  { value: "permanent", label: "Permanent" },
  { value: "visiting", label: "Visiting" },
  { value: "contract", label: "Contract" },
];

const phoneSchema = z
  .string()
  .optional()
  .refine((v) => !v || /^\+?[0-9\s\-()]{7,20}$/.test(v), "Enter a valid phone number");

const schema = z.object({
  employee_code: z.string().min(2, "Employee code is required").max(30),
  name: z.string().min(2, "Name is required").max(150),
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  phone: phoneSchema,
  designation: z.string().min(2, "Designation is required").max(100),
  department_id: z.string().min(1, "Department is required"),
  qualification: z.string().max(100).optional().or(z.literal("")),
  specialization: z.string().max(200).optional().or(z.literal("")),
  date_of_joining: z.string().min(1, "Joining date is required"),
  employment_type: z.enum(["permanent", "visiting", "contract"]),
  max_weekly_hours: z.number({ invalid_type_error: "Required" }).int().min(1).max(40),
});

const updateSchema = z.object({
  name: z.string().min(2).max(150).optional(),
  phone: phoneSchema,
  designation: z.string().min(2).max(100).optional(),
  qualification: z.string().max(100).optional().or(z.literal("")),
  specialization: z.string().max(200).optional().or(z.literal("")),
  employment_type: z.enum(["permanent", "visiting", "contract"]).optional(),
  max_weekly_hours: z.number().int().min(1).max(40).optional(),
});

const fields = [
  { name: "employee_code", label: "Employee code", type: "text", required: true },
  { name: "name", label: "Full name", type: "text", required: true },
  { name: "email", label: "Email", type: "email", required: true },
  { name: "phone", label: "Phone", type: "text" },
  { name: "department_id", label: "Department", type: "select", required: true, optionsSource: departmentOptionsSource },
  { name: "designation", label: "Designation", type: "text", required: true, hint: "e.g. Assistant Professor" },
  { name: "employment_type", label: "Employment type", type: "select", required: true, options: EMPLOYMENT_TYPE_OPTIONS },
  { name: "qualification", label: "Qualification", type: "text", hint: "e.g. Ph.D, M.Tech" },
  { name: "specialization", label: "Specialization", type: "text" },
  { name: "date_of_joining", label: "Date of joining", type: "date", required: true },
  { name: "max_weekly_hours", label: "Max weekly hours", type: "number", required: true, hint: "Default 18" },
];

const editFields = [
  { ...fields[0], disabled: true, hint: "Employee code can't be changed" },
  fields[1],
  { ...fields[2], disabled: true, hint: "Contact Super Admin to change email" },
  fields[3],
  { ...fields[4], disabled: true, hint: "Contact Super Admin to change department" },
  fields[5],
  fields[6],
  fields[7],
  fields[8],
  { ...fields[9], disabled: true },
  fields[10],
];

const columns = [
  { header: "Name", accessorKey: "name", sortKey: "name" },
  { header: "Employee Code", accessorKey: "employee_code", sortKey: "employee_code" },
  { header: "Department", accessorFn: (row) => row.department?.name },
  { header: "Designation", accessorKey: "designation", sortKey: "designation" },
  { header: "Max Hrs/Week", accessorKey: "max_weekly_hours" },
  { header: "Joined", accessorFn: (row) => formatDate(row.date_of_joining), sortKey: "date_of_joining" },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function FacultyPage() {
  return (
    <EntityListPage
      title="Faculty"
      subtitle="Teaching staff and their department assignment."
      queryKey="faculty"
      api={facultyApi}
      entityLabel="Faculty Member"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by name, code or designation…"
      getDefaultValues={(row) => ({
        employee_code: row.employee_code,
        name: row.name,
        email: row.email,
        phone: row.phone ?? "",
        department_id: row.department?.id,
        designation: row.designation,
        employment_type: row.employment_type,
        qualification: row.qualification ?? "",
        specialization: row.specialization ?? "",
        date_of_joining: row.date_of_joining?.slice(0, 10),
        max_weekly_hours: row.max_weekly_hours,
      })}
    />
  );
}
