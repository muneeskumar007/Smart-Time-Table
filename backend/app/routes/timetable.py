from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.repositories.faculty_repository import FacultyRepository
from app.schemas.timetable import (
    AddEntryRequest,
    DeleteEntryRequest,
    GenerateTimetableRequest,
    MoveEntryRequest,
    ReplaceFacultyRequest,
    ReplaceRoomRequest,
    RollbackRequest,
    SwapEntriesRequest,
)
from app.services.manual_edit_service import ManualEditService
from app.services.timetable_generation_service import TimetableGenerationService
from app.services.timetable_service import TimetableService
from app.services.workload_service import RoomAllocationService, WorkloadService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(prefix="/timetable", tags=["Timetable"])

GENERATE_ROLES = (UserRole.SUPER_ADMIN, UserRole.HOD)
PUBLISH_ROLES = (UserRole.SUPER_ADMIN, UserRole.HOD)
ROLLBACK_DELETE_ROLES = (UserRole.SUPER_ADMIN,)


# --- Generation ------------------------------------------------------------


@router.post("/generate", response_model=None)
async def generate_timetable(payload: GenerateTimetableRequest, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    result = await TimetableGenerationService().generate(current_user, payload)
    if result.timetable is None:
        message = "Generation failed - see the response for details"
    elif result.conflicts:
        message = "Timetable generated with conflicts to review before publishing"
    else:
        message = "Timetable generated successfully"
    return success_response(data=result, message=message)


@router.post("/validate", response_model=None)
async def validate_timetable(timetable_id: str, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    result = await TimetableService().validate_timetable(current_user, timetable_id)
    return success_response(data=result, message="Validation complete")


# --- Read --------------------------------------------------------------


@router.get("", response_model=None)
async def list_timetables(
    section_id: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] in (UserRole.FACULTY.value, UserRole.STUDENT.value):
        raise AuthorizationException("Use /timetable/my-timetable or /timetable/section/{id}/published instead")
    items, meta = await TimetableService().list_timetables(current_user, pagination, section_id, status)
    return success_response(data=items, meta=meta, message="Timetables retrieved successfully")


@router.get("/history", response_model=None)
async def get_history(section_id: str, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    items = await TimetableService().get_history(current_user, section_id)
    return success_response(data=items, message="Timetable history retrieved successfully")


@router.get("/section/{section_id}/published", response_model=None)
async def get_published_timetable(section_id: str, current_user: dict = Depends(get_current_user)):
    """Every role may view a published timetable - this is the endpoint
    Students use, per their "view published timetable only" permission."""
    timetable = await TimetableService().get_published_for_section(section_id)
    return success_response(data=timetable, message="Published timetable retrieved successfully")


@router.get("/my-timetable", response_model=None)
async def get_my_timetable(current_user: dict = Depends(get_current_user)):
    """Faculty: their own schedule across whatever sections they teach,
    drawn from each section's published timetable. Students: their
    section's published timetable."""
    if current_user["role"] == UserRole.STUDENT.value:
        if not current_user.get("section_id"):
            raise ValidationException("Your account is not yet assigned to a section - contact your department.")
        timetable = await TimetableService().get_published_for_section(current_user["section_id"])
        return success_response(data=[timetable], message="Your timetable")

    if current_user["role"] == UserRole.FACULTY.value:
        faculty = await FacultyRepository().find_by_email(current_user["email"])
        if not faculty:
            raise NotFoundException("No faculty profile is linked to your account's email address")

        from app.core.constants import Collections
        from app.database.connection import get_database

        db = get_database()
        cursor = db[Collections.TIMETABLES].find({"status": "published", "entries.faculty_id": faculty["id"]})
        my_entries_per_timetable = []
        async for doc in cursor:
            relevant = [e for e in doc.get("entries", []) if e["faculty_id"] == faculty["id"]]
            if relevant:
                my_entries_per_timetable.append({"timetable_id": str(doc["_id"]), "section_id": doc["section_id"], "entries": relevant})
        return success_response(data=my_entries_per_timetable, message="Your teaching schedule")

    raise AuthorizationException("Only Faculty and Student accounts have a personal timetable view")


@router.get("/{timetable_id}", response_model=None)
async def get_timetable(timetable_id: str, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    timetable = await TimetableService().get_timetable(current_user, timetable_id)
    return success_response(data=timetable, message="Timetable retrieved successfully")


# --- Publish / rollback / delete ------------------------------------------


@router.post("/{timetable_id}/publish", response_model=None)
async def publish_timetable(timetable_id: str, current_user: dict = Depends(require_roles(*PUBLISH_ROLES))):
    timetable = await TimetableService().publish(current_user, timetable_id)
    return success_response(data=timetable, message="Timetable published successfully")


@router.post("/rollback", response_model=None)
async def rollback_timetable(payload: RollbackRequest, current_user: dict = Depends(require_roles(*ROLLBACK_DELETE_ROLES))):
    timetable = await TimetableService().rollback(current_user, payload.target_timetable_id)
    return success_response(data=timetable, message="Timetable rolled back successfully")


@router.delete("/{timetable_id}", response_model=None)
async def delete_timetable(timetable_id: str, current_user: dict = Depends(require_roles(*ROLLBACK_DELETE_ROLES))):
    await TimetableService().delete_timetable(current_user, timetable_id)
    return success_response(data=None, message="Timetable deleted successfully")


# --- Manual editor -------------------------------------------------------


@router.post("/{timetable_id}/move", response_model=None)
async def move_entry(timetable_id: str, payload: MoveEntryRequest, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    timetable = await ManualEditService().move_entry(current_user, timetable_id, payload)
    return success_response(data=timetable, message="Session moved successfully")


@router.post("/{timetable_id}/swap", response_model=None)
async def swap_entries(timetable_id: str, payload: SwapEntriesRequest, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    timetable = await ManualEditService().swap_entries(current_user, timetable_id, payload)
    return success_response(data=timetable, message="Sessions swapped successfully")


@router.post("/{timetable_id}/replace-faculty", response_model=None)
async def replace_faculty(
    timetable_id: str, payload: ReplaceFacultyRequest, current_user: dict = Depends(require_roles(*GENERATE_ROLES))
):
    timetable = await ManualEditService().replace_faculty(current_user, timetable_id, payload)
    return success_response(data=timetable, message="Faculty reassigned successfully")


@router.post("/{timetable_id}/replace-room", response_model=None)
async def replace_room(timetable_id: str, payload: ReplaceRoomRequest, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    timetable = await ManualEditService().replace_room(current_user, timetable_id, payload)
    return success_response(data=timetable, message="Room reassigned successfully")


@router.post("/{timetable_id}/add-entry", response_model=None)
async def add_entry(timetable_id: str, payload: AddEntryRequest, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    timetable = await ManualEditService().add_entry(current_user, timetable_id, payload)
    return success_response(data=timetable, message="Session added successfully")


@router.post("/{timetable_id}/delete-entry", response_model=None)
async def delete_entry(timetable_id: str, payload: DeleteEntryRequest, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    timetable = await ManualEditService().delete_entry(current_user, timetable_id, payload)
    return success_response(data=timetable, message="Session removed successfully")


# --- Workload / room allocation -------------------------------------------


@router.get("/workload/faculty/{faculty_id}", response_model=None)
async def get_faculty_workload(faculty_id: str, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    workload = await WorkloadService().get_faculty_workload(current_user, faculty_id)
    return success_response(data=workload, message="Faculty workload retrieved successfully")


@router.get("/workload/department/{department_id}", response_model=None)
async def list_department_workload(department_id: str, current_user: dict = Depends(require_roles(*GENERATE_ROLES))):
    items = await WorkloadService().list_department_workload(current_user, department_id)
    return success_response(data=items, message="Department workload retrieved successfully")


@router.get("/room-allocation/{room_id}", response_model=None)
async def get_room_allocation(
    room_id: str, academic_year_id: str, semester_id: str, current_user: dict = Depends(require_roles(*GENERATE_ROLES))
):
    allocation = await RoomAllocationService().get_room_allocation(room_id, academic_year_id, semester_id)
    return success_response(data=allocation, message="Room allocation retrieved successfully")
