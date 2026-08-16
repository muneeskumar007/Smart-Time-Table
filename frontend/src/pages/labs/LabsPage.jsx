import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge, Badge } from "../../components/common/Badge";
import { labApi, departmentApi } from "../../services/api/entities";
import { useAuth } from "../../context/AuthContext";
import { ROLES } from "../../constants";

const departmentOptionsSource = { queryKey: ["departments", "lookup"], fetcher: () => departmentApi.lookup() };

const schema = z.object({
  lab_name: z.string().min(2, "Lab name is required").max(150),
  room_number: z.string().min(1, "Room number is required").max(20),
  department_id: z.string().min(1, "Department is required"),
  capacity: z.number({ invalid_type_error: "Capacity is required" }).int().min(1).max(300),
  available_systems: z
    .union([z.number(), z.nan()])
    .optional()
    .transform((v) => (Number.isNaN(v) ? undefined : v)),
  building: z.string().max(100).optional().or(z.literal("")),
  floor: z.string().max(20).optional().or(z.literal("")),
  has_ac: z.boolean().optional(),
});

const updateSchema = z.object({
  lab_name: z.string().min(2).max(150).optional(),
  capacity: z.number().int().min(1).max(300).optional(),
  available_systems: z
    .union([z.number(), z.nan()])
    .optional()
    .transform((v) => (Number.isNaN(v) ? undefined : v)),
  building: z.string().max(100).optional().or(z.literal("")),
  floor: z.string().max(20).optional().or(z.literal("")),
  has_ac: z.boolean().optional(),
});

const fields = [
  { name: "lab_name", label: "Lab name", type: "text", required: true, hint: "e.g. Computer Lab 1" },
  { name: "room_number", label: "Room number", type: "text", required: true },
  { name: "department_id", label: "Department", type: "select", required: true, optionsSource: departmentOptionsSource },
  { name: "capacity", label: "Capacity", type: "number", required: true },
  { name: "available_systems", label: "Available systems", type: "number", hint: "Number of working computers/workstations" },
  { name: "building", label: "Building", type: "text" },
  { name: "floor", label: "Floor", type: "text" },
  { name: "has_ac", label: "Has air conditioning", type: "checkbox" },
];

const editFields = [
  fields[0],
  { ...fields[1], disabled: true, hint: "Room number can't be changed after creation" },
  ...fields.slice(3),
];

const columns = [
  { header: "Lab", accessorKey: "lab_name", sortKey: "lab_name" },
  { header: "Room", accessorKey: "room_number", sortKey: "room_number" },
  { header: "Department", accessorFn: (row) => row.department?.name },
  { header: "Capacity", accessorKey: "capacity", sortKey: "capacity" },
  { header: "Systems", accessorFn: (row) => row.available_systems ?? "—" },
  {
    header: "Amenities",
    accessorFn: (row) => row,
    cell: (info) => (info.getValue().has_ac ? <Badge>AC</Badge> : "—"),
  },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function LabsPage() {
  const { user } = useAuth();
  const extraParams = user?.role === ROLES.HOD ? { department_id: user.department_id } : {};

  return (
    <EntityListPage
      title="Laboratories"
      subtitle="Lab rooms used for practical/lab sessions."
      queryKey="labs"
      api={labApi}
      entityLabel="Laboratory"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by lab name or room number…"
      extraParams={extraParams}
    />
  );
}
