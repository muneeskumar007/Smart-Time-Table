import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge, Badge } from "../../components/common/Badge";
import { subjectApi, courseApi } from "../../services/api/entities";

const courseOptionsSource = { queryKey: ["courses", "lookup"], fetcher: () => courseApi.lookup() };

const SUBJECT_TYPE_OPTIONS = [
  { value: "theory", label: "Theory" },
  { value: "lab", label: "Lab" },
  { value: "elective", label: "Elective" },
  { value: "project", label: "Project" },
];

const schema = z.object({
  name: z.string().min(2, "Name is required").max(150),
  code: z.string().min(2, "Code is required").max(30),
  course_id: z.string().min(1, "Course is required"),
  semester_number: z.number({ invalid_type_error: "Required" }).int().min(1).max(20),
  credits: z.number({ invalid_type_error: "Required" }).min(0).max(20),
  subject_type: z.enum(["theory", "lab", "elective", "project"]),
  weekly_lecture_hours: z.number({ invalid_type_error: "Required" }).int().min(0).max(20),
  weekly_lab_hours: z.number().int().min(0).max(20).optional(),
});

const updateSchema = z.object({
  name: z.string().min(2).max(150).optional(),
  semester_number: z.number().int().min(1).max(20).optional(),
  credits: z.number().min(0).max(20).optional(),
  subject_type: z.enum(["theory", "lab", "elective", "project"]).optional(),
  weekly_lecture_hours: z.number().int().min(0).max(20).optional(),
  weekly_lab_hours: z.number().int().min(0).max(20).optional(),
});

const fields = [
  { name: "name", label: "Subject name", type: "text", required: true },
  { name: "code", label: "Code", type: "text", required: true, hint: "e.g. CS301" },
  { name: "course_id", label: "Course", type: "select", required: true, optionsSource: courseOptionsSource },
  { name: "semester_number", label: "Curriculum semester", type: "number", required: true, hint: "Which semester of the course this belongs to" },
  { name: "subject_type", label: "Subject type", type: "select", required: true, options: SUBJECT_TYPE_OPTIONS },
  { name: "credits", label: "Credits", type: "number", required: true },
  { name: "weekly_lecture_hours", label: "Weekly lecture hours", type: "number", required: true },
  { name: "weekly_lab_hours", label: "Weekly lab hours", type: "number", hint: "Leave 0 if this subject has no lab component" },
];

const editFields = [
  fields[0],
  { ...fields[1], disabled: true, hint: "Code can't be changed after creation" },
  { ...fields[2], disabled: true, hint: "Contact Super Admin to change course" },
  ...fields.slice(3),
];

const columns = [
  { header: "Subject", accessorKey: "name", sortKey: "name" },
  { header: "Code", accessorKey: "code", sortKey: "code" },
  { header: "Sem.", accessorKey: "semester_number", sortKey: "semester_number" },
  { header: "Type", accessorFn: (row) => SUBJECT_TYPE_OPTIONS.find((o) => o.value === row.subject_type)?.label },
  { header: "Credits", accessorKey: "credits", sortKey: "credits" },
  {
    header: "Hours/Week",
    accessorFn: (row) => row,
    cell: (info) => {
      const s = info.getValue();
      return (
        <div className="flex gap-1.5">
          <Badge>{s.weekly_lecture_hours} lecture</Badge>
          {s.weekly_lab_hours > 0 && <Badge variant="brand">{s.weekly_lab_hours} lab</Badge>}
        </div>
      );
    },
  },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function SubjectsPage() {
  return (
    <EntityListPage
      title="Subjects"
      subtitle="Curriculum subjects taught within each course."
      queryKey="subjects"
      api={subjectApi}
      entityLabel="Subject"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by name or code…"
      getDefaultValues={(row) => ({
        name: row.name,
        code: row.code,
        course_id: row.course?.id,
        semester_number: row.semester_number,
        subject_type: row.subject_type,
        credits: row.credits,
        weekly_lecture_hours: row.weekly_lecture_hours,
        weekly_lab_hours: row.weekly_lab_hours,
      })}
    />
  );
}
