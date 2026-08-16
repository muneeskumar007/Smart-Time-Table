import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge } from "../../components/common/Badge";
import { courseApi, departmentApi } from "../../services/api/entities";

const departmentOptionsSource = { queryKey: ["departments", "lookup"], fetcher: () => departmentApi.lookup() };

const schema = z.object({
  name: z.string().min(2, "Name is required").max(150),
  code: z.string().min(2, "Code is required").max(30),
  department_id: z.string().min(1, "Department is required"),
  duration_years: z.number({ invalid_type_error: "Required" }).int().min(1).max(10),
  total_semesters: z.number({ invalid_type_error: "Required" }).int().min(1).max(20),
  description: z.string().max(1000).optional().or(z.literal("")),
});

const updateSchema = z.object({
  name: z.string().min(2).max(150).optional(),
  duration_years: z.number().int().min(1).max(10).optional(),
  total_semesters: z.number().int().min(1).max(20).optional(),
  description: z.string().max(1000).optional().or(z.literal("")),
});

const fields = [
  { name: "name", label: "Course name", type: "text", required: true, hint: "e.g. B.Tech Computer Science & Engineering" },
  { name: "code", label: "Code", type: "text", required: true, hint: "e.g. BTECH-CSE" },
  { name: "department_id", label: "Department", type: "select", required: true, optionsSource: departmentOptionsSource },
  { name: "duration_years", label: "Duration (years)", type: "number", required: true },
  { name: "total_semesters", label: "Total semesters", type: "number", required: true },
  { name: "description", label: "Description", type: "textarea" },
];

const editFields = [
  fields[0],
  { ...fields[1], disabled: true, hint: "Code can't be changed after creation" },
  { ...fields[2], disabled: true, hint: "Contact Super Admin to change department" },
  fields[3],
  fields[4],
  fields[5],
];

const columns = [
  { header: "Course", accessorKey: "name", sortKey: "name" },
  { header: "Code", accessorKey: "code", sortKey: "code" },
  { header: "Department", accessorFn: (row) => row.department?.name },
  { header: "Duration", accessorFn: (row) => `${row.duration_years} yr` },
  { header: "Semesters", accessorKey: "total_semesters" },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function CoursesPage() {
  return (
    <EntityListPage
      title="Courses"
      subtitle="Academic programmes offered by each department."
      queryKey="courses"
      api={courseApi}
      entityLabel="Course"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by name or code…"
      getDefaultValues={(row) => ({
        name: row.name,
        code: row.code,
        department_id: row.department?.id,
        duration_years: row.duration_years,
        total_semesters: row.total_semesters,
        description: row.description ?? "",
      })}
    />
  );
}
