import { z } from "zod";
import { EntityListPage } from "../../components/crud/EntityListPage";
import { ActiveBadge, Badge } from "../../components/common/Badge";
import { roomApi } from "../../services/api/entities";

const ROOM_TYPE_OPTIONS = [
  { value: "classroom", label: "Classroom" },
  { value: "seminar_hall", label: "Seminar Hall" },
  { value: "auditorium", label: "Auditorium" },
];

const schema = z.object({
  room_number: z.string().min(1, "Room number is required").max(20),
  building: z.string().max(100).optional().or(z.literal("")),
  floor: z.string().max(20).optional().or(z.literal("")),
  capacity: z.number({ invalid_type_error: "Capacity is required" }).int().min(1).max(1000),
  room_type: z.enum(["classroom", "seminar_hall", "auditorium"]),
  has_projector: z.boolean().optional(),
  has_ac: z.boolean().optional(),
});

const updateSchema = z.object({
  building: z.string().max(100).optional().or(z.literal("")),
  floor: z.string().max(20).optional().or(z.literal("")),
  capacity: z.number().int().min(1).max(1000).optional(),
  room_type: z.enum(["classroom", "seminar_hall", "auditorium"]).optional(),
  has_projector: z.boolean().optional(),
  has_ac: z.boolean().optional(),
});

const fields = [
  { name: "room_number", label: "Room number", type: "text", required: true },
  { name: "room_type", label: "Room type", type: "select", required: true, options: ROOM_TYPE_OPTIONS },
  { name: "capacity", label: "Capacity", type: "number", required: true },
  { name: "building", label: "Building", type: "text" },
  { name: "floor", label: "Floor", type: "text" },
  { name: "has_projector", label: "Has projector", type: "checkbox" },
  { name: "has_ac", label: "Has air conditioning", type: "checkbox" },
];

const editFields = [
  { ...fields[0], disabled: true, hint: "Room number can't be changed after creation" },
  ...fields.slice(1),
];

const columns = [
  { header: "Room", accessorKey: "room_number", sortKey: "room_number" },
  { header: "Type", accessorFn: (row) => ROOM_TYPE_OPTIONS.find((o) => o.value === row.room_type)?.label ?? row.room_type },
  { header: "Capacity", accessorKey: "capacity", sortKey: "capacity" },
  { header: "Building", accessorFn: (row) => row.building ?? "—" },
  {
    header: "Amenities",
    accessorFn: (row) => row,
    cell: (info) => {
      const room = info.getValue();
      return (
        <div className="flex gap-1.5">
          {room.has_projector && <Badge>Projector</Badge>}
          {room.has_ac && <Badge>AC</Badge>}
          {!room.has_projector && !room.has_ac && "—"}
        </div>
      );
    },
  },
  { header: "Status", accessorFn: (row) => row, cell: (info) => <ActiveBadge isActive={info.getValue().is_active} /> },
];

export default function RoomsPage() {
  return (
    <EntityListPage
      title="Rooms"
      subtitle="Classrooms, seminar halls and auditoria shared across the institution."
      queryKey="rooms"
      api={roomApi}
      entityLabel="Room"
      columns={columns}
      fields={fields}
      editFields={editFields}
      schema={schema}
      updateSchema={updateSchema}
      searchPlaceholder="Search by room number or building…"
    />
  );
}
