import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { Badge } from "../../components/common/Badge";
import { timeslotApi, departmentApi } from "../../services/api/entities";
import { useAuth } from "../../context/AuthContext";
import { ROLES } from "../../constants";
import { formatTime } from "../../utils";

const departmentOptionsSource = { queryKey: ["departments", "lookup"], fetcher: () => departmentApi.lookup() };

const DAY_OPTIONS = [
  { value: "MON", label: "Monday" },
  { value: "TUE", label: "Tuesday" },
  { value: "WED", label: "Wednesday" },
  { value: "THU", label: "Thursday" },
  { value: "FRI", label: "Friday" },
  { value: "SAT", label: "Saturday" },
];

const timeSchema = z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/, "Use 24-hour HH:MM format");

const baseSchema = z.object({
  day_of_week: z.enum(["MON", "TUE", "WED", "THU", "FRI", "SAT"]),
  start_time: timeSchema,
  end_time: timeSchema,
  label: z.string().max(50).optional().or(z.literal("")),
  slot_order: z.number().int().min(0).max(50).optional(),
  is_break: z.boolean().optional(),
});

const schema = baseSchema
  .extend({ department_id: z.string().optional().or(z.literal("")) })
  .refine((d) => d.end_time > d.start_time, { message: "End time must be after start time", path: ["end_time"] });

const updateSchema = z.object({
  day_of_week: z.enum(["MON", "TUE", "WED", "THU", "FRI", "SAT"]).optional(),
  start_time: timeSchema.optional(),
  end_time: timeSchema.optional(),
  label: z.string().max(50).optional().or(z.literal("")),
  slot_order: z.number().int().min(0).max(50).optional(),
  is_break: z.boolean().optional(),
});

function useFields() {
  const { user } = useAuth();
  const base = [
    { name: "day_of_week", label: "Day", type: "select", required: true, options: DAY_OPTIONS },
    { name: "start_time", label: "Start time", type: "time", required: true },
    { name: "end_time", label: "End time", type: "time", required: true },
    { name: "label", label: "Period label", type: "text", hint: "e.g. Period 1" },
    { name: "slot_order", label: "Display order", type: "number", hint: "Controls left-to-right order in the grid" },
    { name: "is_break", label: "This is a break period (e.g. lunch)", type: "checkbox" },
  ];
  if (user?.role === ROLES.SUPER_ADMIN) {
    return [
      ...base,
      {
        name: "department_id",
        label: "Department",
        type: "select",
        optionsSource: departmentOptionsSource,
        hint: "Leave blank to create a slot shared by every department",
      },
    ];
  }
  return base;
}

const columns = [
  { header: "Day", accessorFn: (row) => DAY_OPTIONS.find((d) => d.value === row.day_of_week)?.label, sortKey: "day_of_week" },
  { header: "Time", accessorFn: (row) => `${formatTime(row.start_time)} - ${formatTime(row.end_time)}`, sortKey: "start_time" },
  { header: "Label", accessorFn: (row) => row.label ?? "—" },
  {
    header: "Type",
    accessorFn: (row) => row,
    cell: (info) => (info.getValue().is_break ? <Badge variant="warning">Break</Badge> : <Badge variant="brand">Class</Badge>),
  },
  { header: "Scope", accessorFn: (row) => row.department?.name ?? "Global (all departments)" },
];

export default function TimeSlotsPage() {
  const fields = useFields();
  const { user } = useAuth();
  const extraParams = user?.role === ROLES.HOD ? { department_id: user.department_id } : {};

  return (
    <EntityListPage
      title="Time Slots"
      subtitle="The weekly period grid classes are scheduled against."
      queryKey="timeslots"
      api={timeslotApi}
      entityLabel="Time Slot"
      columns={columns}
      fields={fields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by label…"
      extraParams={extraParams}
      getDefaultValues={(row) => ({
        day_of_week: row.day_of_week,
        start_time: row.start_time,
        end_time: row.end_time,
        label: row.label ?? "",
        slot_order: row.slot_order,
        is_break: row.is_break,
      })}
    />
  );
}
