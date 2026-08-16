import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge } from "../../components/common/Badge";
import { sectionApi, courseApi, academicYearApi, semesterApi, facultyApi, roomApi } from "../../services/api/entities";

const courseOptionsSource = { queryKey: ["courses", "lookup"], fetcher: () => courseApi.lookup() };
const yearOptionsSource = { queryKey: ["academic-years", "lookup"], fetcher: () => academicYearApi.lookup() };
const semesterOptionsSource = { queryKey: ["semesters", "lookup"], fetcher: () => semesterApi.lookup() };
const facultyOptionsSource = { queryKey: ["faculty", "lookup"], fetcher: () => facultyApi.lookup() };
const roomOptionsSource = { queryKey: ["rooms", "lookup"], fetcher: () => roomApi.lookup(), labelKey: "room_number" };

const schema = z.object({
  course_id: z.string().min(1, "Course is required"),
  academic_year_id: z.string().min(1, "Academic year is required"),
  semester_id: z.string().min(1, "Semester is required"),
  semester_number: z.number({ invalid_type_error: "Required" }).int().min(1).max(20),
  section_name: z.string().min(1, "Section name is required").max(10),
  strength: z.number({ invalid_type_error: "Required" }).int().min(1).max(500),
  class_advisor_id: z.string().optional().or(z.literal("")),
  room_id: z.string().optional().or(z.literal("")),
});

const updateSchema = z.object({
  strength: z.number().int().min(1).max(500).optional(),
  class_advisor_id: z.string().optional().or(z.literal("")),
  room_id: z.string().optional().or(z.literal("")),
});

const fields = [
  { name: "course_id", label: "Course", type: "select", required: true, optionsSource: courseOptionsSource },
  { name: "academic_year_id", label: "Academic year", type: "select", required: true, optionsSource: yearOptionsSource },
  { name: "semester_id", label: "Semester (term)", type: "select", required: true, optionsSource: semesterOptionsSource },
  {
    name: "semester_number",
    label: "Curriculum semester",
    type: "number",
    required: true,
    hint: "Which semester of the course these students are in",
  },
  { name: "section_name", label: "Section name", type: "text", required: true, hint: "e.g. A, B, C" },
  { name: "strength", label: "Student strength", type: "number", required: true },
  { name: "class_advisor_id", label: "Class advisor", type: "select", optionsSource: facultyOptionsSource },
  { name: "room_id", label: "Home room", type: "select", optionsSource: roomOptionsSource },
];

const editFields = [
  { ...fields[0], disabled: true },
  { ...fields[1], disabled: true },
  { ...fields[2], disabled: true },
  { ...fields[3], disabled: true },
  { ...fields[4], disabled: true, hint: "Contact Super Admin to change these identifying details" },
  fields[5],
  fields[6],
  fields[7],
];

const columns = [
  { header: "Section", accessorFn: (row) => row.display_name ?? `${row.course?.name} - ${row.section_name}` },
  { header: "Course", accessorFn: (row) => row.course?.name },
  { header: "Sem.", accessorKey: "semester_number" },
  { header: "Strength", accessorKey: "strength", sortKey: "strength" },
  { header: "Class Advisor", accessorFn: (row) => row.class_advisor?.name ?? "—" },
  { header: "Room", accessorFn: (row) => row.room?.name ?? "—" },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function SectionsPage() {
  return (
    <EntityListPage
      title="Sections"
      subtitle="Student batches within a course, tied to a specific term."
      queryKey="sections"
      api={sectionApi}
      entityLabel="Section"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by section name…"
      transformSubmit={(data) => ({
        ...data,
        class_advisor_id: data.class_advisor_id || null,
        room_id: data.room_id || null,
      })}
      getDefaultValues={(row) => ({
        course_id: row.course?.id,
        academic_year_id: row.academic_year?.id,
        semester_id: row.semester?.id,
        semester_number: row.semester_number,
        section_name: row.section_name,
        strength: row.strength,
        class_advisor_id: row.class_advisor?.id ?? "",
        room_id: row.room?.id ?? "",
      })}
    />
  );
}
