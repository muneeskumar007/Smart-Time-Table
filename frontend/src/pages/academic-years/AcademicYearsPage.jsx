import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { Badge, ActiveBadge } from "../../components/common/Badge";
import { academicYearApi } from "../../services/api/entities";
import { formatDate } from "../../utils";

const schema = z
  .object({
    name: z.string().min(4, "e.g. 2026-2027").max(20),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().min(1, "End date is required"),
  })
  .refine((d) => new Date(d.end_date) > new Date(d.start_date), {
    message: "End date must be after start date",
    path: ["end_date"],
  });

const updateSchema = z.object({
  name: z.string().min(4).max(20).optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  is_current: z.boolean().optional(),
});

const fields = [
  { name: "name", label: "Academic year", type: "text", required: true, hint: "e.g. 2026-2027" },
  { name: "start_date", label: "Start date", type: "date", required: true },
  { name: "end_date", label: "End date", type: "date", required: true },
];

const editFields = [...fields, { name: "is_current", label: "Set as the current academic year", type: "checkbox" }];

const columns = [
  { header: "Academic Year", accessorKey: "name", sortKey: "name" },
  { header: "Start Date", accessorFn: (row) => formatDate(row.start_date), sortKey: "start_date" },
  { header: "End Date", accessorFn: (row) => formatDate(row.end_date) },
  {
    header: "Current",
    accessorFn: (row) => row,
    cell: (info) => (info.getValue().is_current ? <Badge variant="brand">Current</Badge> : "—"),
  },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function AcademicYearsPage() {
  return (
    <EntityListPage
      title="Academic Years"
      subtitle="Define the academic years scheduling runs against."
      queryKey="academic-years"
      api={academicYearApi}
      entityLabel="Academic Year"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search academic years…"
      getDefaultValues={(row) => ({
        name: row.name,
        start_date: row.start_date?.slice(0, 10),
        end_date: row.end_date?.slice(0, 10),
        is_current: row.is_current,
      })}
    />
  );
}
