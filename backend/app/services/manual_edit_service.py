"""
Manual timetable editor.

Every operation follows the same shape: load the timetable, compute the
proposed new entries[] in memory, run the *exact same*
ConflictDetectionService used by generation and the standalone validate
endpoint against the proposed result, and only persist if it comes back
clean - "Validate after every change. Reject invalid edits." from the
brief, satisfied by reusing rules rather than re-implementing them.

Editing a PUBLISHED timetable knocks its status back to DRAFT: a
published-and-then-edited schedule is an unreviewed change and
shouldn't keep being served as "the official published timetable" to
students/faculty until someone re-approves it via publish() again.
"""
from app.auth.dependencies import ensure_department_access
from app.core.exceptions import NotFoundException, ValidationException
from app.models.timetable import AuditLogEntry, TimetableStatus
from app.repositories.academic_structure_repository import SectionRepository
from app.repositories.lab_repository import LabRepository
from app.repositories.timetable_repository import TimetableRepository
from app.schemas.timetable import (
    AddEntryRequest,
    DeleteEntryRequest,
    MoveEntryRequest,
    ReplaceFacultyRequest,
    ReplaceRoomRequest,
    SwapEntriesRequest,
    TimetableResponse,
)
from app.services.conflict_detection_service import ConflictDetectionService
from app.services.timetable_generation_service import TimetableGenerationService
from app.services.timetable_service import build_timetable_response

EDITABLE_STATUSES = {TimetableStatus.DRAFT.value, TimetableStatus.GENERATED.value, TimetableStatus.PUBLISHED.value}


class ManualEditService:
    def __init__(self):
        self.repo = TimetableRepository()

    async def _load_editable(self, current_user: dict, timetable_id: str) -> dict:
        doc = await self.repo.get_by_id_or_404(timetable_id)
        ensure_department_access(current_user, doc["department_id"])
        if doc["status"] not in EDITABLE_STATUSES:
            raise ValidationException(f"A timetable with status '{doc['status']}' cannot be edited")
        return doc

    def _find_entry(self, entries: list[dict], timeslot_id: str) -> dict:
        for entry in entries:
            if entry["timeslot_id"] == timeslot_id:
                return entry
        raise NotFoundException(f"No session is scheduled at time slot {timeslot_id}")

    async def _validate_and_save(self, current_user: dict, doc: dict, new_entries: list[dict], action: str, details: str) -> TimetableResponse:
        section = await SectionRepository().get_by_id_or_404(doc["section_id"])
        ctx = await TimetableGenerationService()._load_context(section)
        # A manual edit may reference a timeslot/room/faculty outside
        # what the generator considered eligible (e.g. a slot that was
        # externally-occupied at generation time but has since freed up)
        # - re-fetching a fresh context keeps validation accurate rather
        # than reusing stale eligibility from whenever this was generated.

        validation = ConflictDetectionService().validate_entries(new_entries, ctx)
        if not validation.is_valid:
            raise ValidationException(
                "This change would create a conflict and was not applied.",
                errors=[{"field": c.type, "message": c.message} for c in validation.conflicts],
            )

        new_status = TimetableStatus.DRAFT.value if doc["status"] == TimetableStatus.PUBLISHED.value else doc["status"]
        updated = await self.repo.update(
            doc["id"],
            {
                "entries": new_entries,
                "status": new_status,
                "audit_log": [
                    *doc.get("audit_log", []),
                    AuditLogEntry(action=action, actor_id=current_user["id"], details=details).model_dump(),
                ],
            },
            actor_id=current_user["id"],
        )
        return await build_timetable_response(updated)

    async def move_entry(self, current_user: dict, timetable_id: str, payload: MoveEntryRequest) -> TimetableResponse:
        doc = await self._load_editable(current_user, timetable_id)
        entries = list(doc.get("entries", []))
        entry = self._find_entry(entries, payload.from_timeslot_id)

        section = await SectionRepository().get_by_id_or_404(doc["section_id"])
        ctx = await TimetableGenerationService()._load_context(section)
        target_slot = ctx.timeslots_by_id.get(payload.to_timeslot_id)
        if not target_slot:
            raise ValidationException("The target time slot does not exist or is not available to this department")

        new_entries = [e for e in entries if e["timeslot_id"] != payload.from_timeslot_id]
        new_entries.append(
            {
                **entry,
                "timeslot_id": payload.to_timeslot_id,
                "day_of_week": target_slot["day_of_week"],
                "period_label": target_slot.get("label"),
                "start_time": target_slot["start_time"],
                "end_time": target_slot["end_time"],
            }
        )
        return await self._validate_and_save(
            current_user, doc, new_entries, "edited", f"Moved a session from {payload.from_timeslot_id} to {payload.to_timeslot_id}"
        )

    async def swap_entries(self, current_user: dict, timetable_id: str, payload: SwapEntriesRequest) -> TimetableResponse:
        doc = await self._load_editable(current_user, timetable_id)
        entries = list(doc.get("entries", []))
        entry_a = self._find_entry(entries, payload.timeslot_id_a)
        entry_b = self._find_entry(entries, payload.timeslot_id_b)

        slot_fields = ("timeslot_id", "day_of_week", "period_label", "start_time", "end_time")
        new_entries = []
        for entry in entries:
            if entry["timeslot_id"] == payload.timeslot_id_a:
                new_entries.append({**entry, **{f: entry_b[f] for f in slot_fields}})
            elif entry["timeslot_id"] == payload.timeslot_id_b:
                new_entries.append({**entry, **{f: entry_a[f] for f in slot_fields}})
            else:
                new_entries.append(entry)

        return await self._validate_and_save(
            current_user, doc, new_entries, "edited", f"Swapped sessions at {payload.timeslot_id_a} and {payload.timeslot_id_b}"
        )

    async def replace_faculty(self, current_user: dict, timetable_id: str, payload: ReplaceFacultyRequest) -> TimetableResponse:
        doc = await self._load_editable(current_user, timetable_id)
        entries = list(doc.get("entries", []))
        self._find_entry(entries, payload.timeslot_id)

        new_entries = [
            {**e, "faculty_id": payload.new_faculty_id} if e["timeslot_id"] == payload.timeslot_id else e for e in entries
        ]
        return await self._validate_and_save(
            current_user, doc, new_entries, "edited", f"Reassigned faculty for session at {payload.timeslot_id}"
        )

    async def replace_room(self, current_user: dict, timetable_id: str, payload: ReplaceRoomRequest) -> TimetableResponse:
        doc = await self._load_editable(current_user, timetable_id)
        entries = list(doc.get("entries", []))
        self._find_entry(entries, payload.timeslot_id)

        new_entries = [
            {**e, "room_id": payload.new_room_id} if e["timeslot_id"] == payload.timeslot_id else e for e in entries
        ]
        return await self._validate_and_save(
            current_user, doc, new_entries, "edited", f"Reassigned room for session at {payload.timeslot_id}"
        )

    async def add_entry(self, current_user: dict, timetable_id: str, payload: AddEntryRequest) -> TimetableResponse:
        doc = await self._load_editable(current_user, timetable_id)
        entries = list(doc.get("entries", []))
        if any(e["timeslot_id"] == payload.timeslot_id for e in entries):
            raise ValidationException("This time slot is already occupied - remove the existing session first or choose another slot")

        section = await SectionRepository().get_by_id_or_404(doc["section_id"])
        ctx = await TimetableGenerationService()._load_context(section)
        slot = ctx.timeslots_by_id.get(payload.timeslot_id)
        if not slot:
            raise ValidationException("The selected time slot does not exist or is not available to this department")

        is_lab = await LabRepository().find_by_id(payload.room_id) is not None

        new_entries = [
            *entries,
            {
                "timeslot_id": payload.timeslot_id,
                "day_of_week": slot["day_of_week"],
                "period_label": slot.get("label"),
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "subject_id": payload.subject_id,
                "faculty_id": payload.faculty_id,
                "room_id": payload.room_id,
                "is_lab": is_lab,
                "remarks": payload.remarks,
            },
        ]
        return await self._validate_and_save(current_user, doc, new_entries, "edited", f"Added a session at {payload.timeslot_id}")

    async def delete_entry(self, current_user: dict, timetable_id: str, payload: DeleteEntryRequest) -> TimetableResponse:
        doc = await self._load_editable(current_user, timetable_id)
        entries = list(doc.get("entries", []))
        self._find_entry(entries, payload.timeslot_id)  # 404s if not present

        new_entries = [e for e in entries if e["timeslot_id"] != payload.timeslot_id]
        # Deleting can never introduce a NEW conflict, so this skips
        # re-validation (unlike every other edit above) - it only needs
        # the status-downgrade-on-published-edit + audit logging that
        # _validate_and_save would otherwise also give it.
        new_status = TimetableStatus.DRAFT.value if doc["status"] == TimetableStatus.PUBLISHED.value else doc["status"]
        updated = await self.repo.update(
            doc["id"],
            {
                "entries": new_entries,
                "status": new_status,
                "audit_log": [
                    *doc.get("audit_log", []),
                    AuditLogEntry(action="edited", actor_id=current_user["id"], details=f"Deleted session at {payload.timeslot_id}").model_dump(),
                ],
            },
            actor_id=current_user["id"],
        )
        return await build_timetable_response(updated)
