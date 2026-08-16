import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge } from "../../components/common/Badge";
import { departmentApi } from "../../services/api/entities";
import { formatDate } from "../../utils";

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(150),
  code: z.string().min(2, "Code must be at least 2 characters").max(20),
  description: z.string().max(1000).optional().or(z.literal("")),
  established_year: z
    .union([z.number(), z.nan()])
    .optional()
    .transform((v) => (Number.isNaN(v) ? undefined : v)),
});

const fields = [
  { name: "name", label: "Department name", type: "text", required: true },
  { name: "code", label: "Code", type: "text", required: true, hint: "e.g. CSE, ECE" },
  { name: "established_year", label: "Established year", type: "number" },
  { name: "description", label: "Description", type: "textarea" },
];

const columns = [
  { header: "Name", accessorKey: "name", sortKey: "name" },
  { header: "Code", accessorKey: "code", sortKey: "code" },
  { header: "Faculty", accessorFn: (row) => row.faculty_count },
  { header: "Courses", accessorFn: (row) => row.course_count },
  { header: "Sections", accessorFn: (row) => row.section_count },
  { header: "Established", accessorFn: (row) => row.established_year ?? "—" },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
  { header: "Created", accessorFn: (row) => formatDate(row.created_at) },
];

export default function DepartmentsPage() {
  return (
    <EntityListPage
      title="Departments"
      subtitle="Manage the academic departments in your institution."
      queryKey="departments"
      api={departmentApi}
      entityLabel="Department"
      columns={columns}
      fields={fields}
      schema={schema}
      searchPlaceholder="Search by name or code…"
    />
  );
}
