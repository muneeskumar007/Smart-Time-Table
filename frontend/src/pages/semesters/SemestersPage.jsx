import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { Badge, ActiveBadge } from "../../components/common/Badge";
import { semesterApi, academicYearApi } from "../../services/api/entities";
import { formatDate } from "../../utils";

const schema = z
  .object({
    name: z.string().min(2, "Name is required").max(50),
    academic_year_id: z.string().min(1, "Academic year is required"),
    term_type: z.enum(["odd", "even"], { errorMap: () => ({ message: "Select a term type" }) }),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().min(1, "End date is required"),
  })
  .refine((d) => new Date(d.end_date) > new Date(d.start_date), {
    message: "End date must be after start date",
    path: ["end_date"],
  });

const updateSchema = z.object({
  name: z.string().min(2).max(50).optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  is_current: z.boolean().optional(),
});

const academicYearOptionsSource = { queryKey: ["academic-years", "lookup"], fetcher: () => academicYearApi.lookup() };

const fields = [
  { name: "name", label: "Semester name", type: "text", required: true, hint: "e.g. Odd Semester 2026-27" },
  { name: "academic_year_id", label: "Academic year", type: "select", required: true, optionsSource: academicYearOptionsSource },
  {
    name: "term_type",
    label: "Term",
    type: "select",
    required: true,
    options: [
      { value: "odd", label: "Odd" },
      { value: "even", label: "Even" },
    ],
  },
  { name: "start_date", label: "Start date", type: "date", required: true },
  { name: "end_date", label: "End date", type: "date", required: true },
];

const editFields = [
  fields[0],
  fields[3],
  fields[4],
  { name: "is_current", label: "Set as the current semester", type: "checkbox" },
];

const columns = [
  { header: "Semester", accessorKey: "name", sortKey: "name" },
  { header: "Academic Year", accessorFn: (row) => row.academic_year?.name },
  { header: "Term", accessorFn: (row) => (row.term_type === "odd" ? "Odd" : "Even") },
  { header: "Start Date", accessorFn: (row) => formatDate(row.start_date), sortKey: "start_date" },
  { header: "End Date", accessorFn: (row) => formatDate(row.end_date) },
  {
    header: "Current",
    accessorFn: (row) => row,
    cell: (info) => (info.getValue().is_current ? <Badge variant="brand">Current</Badge> : "—"),
  },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function SemestersPage() {
  return (
    <EntityListPage
      title="Semesters"
      subtitle="Schedulable terms within each academic year."
      queryKey="semesters"
      api={semesterApi}
      entityLabel="Semester"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search semesters…"
      getDefaultValues={(row) => ({
        name: row.name,
        start_date: row.start_date?.slice(0, 10),
        end_date: row.end_date?.slice(0, 10),
        is_current: row.is_current,
      })}
    />
  );
}
