from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.schemas.academic_calendar import (
    AcademicYearCreate,
    AcademicYearUpdate,
    SemesterCreate,
    SemesterUpdate,
    TimeSlotCreate,
    TimeSlotUpdate,
)
from app.services.academic_calendar_service import AcademicYearService, SemesterService, TimeSlotService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(tags=["Academic Calendar"])

# --- Academic Years (institution-wide -> Super Admin manages, everyone reads) ---

years_router = APIRouter(prefix="/academic-years")


@years_router.get("", response_model=None)
async def list_academic_years(
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await AcademicYearService().list_years(pagination, include_inactive)
    return success_response(data=items, meta=meta, message="Academic years retrieved successfully")


@years_router.get("/lookup", response_model=None)
async def lookup_academic_years(current_user: dict = Depends(get_current_user)):
    items = await AcademicYearService().list_all_active()
    return success_response(data=items, message="Academic years retrieved successfully")


@years_router.get("/{year_id}", response_model=None)
async def get_academic_year(year_id: str, current_user: dict = Depends(get_current_user)):
    year = await AcademicYearService().get_year(year_id)
    return success_response(data=year, message="Academic year retrieved successfully")


@years_router.post("", response_model=None, status_code=201)
async def create_academic_year(payload: AcademicYearCreate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    year = await AcademicYearService().create_year(current_user, payload)
    return success_response(data=year, message="Academic year created successfully")


@years_router.patch("/{year_id}", response_model=None)
async def update_academic_year(
    year_id: str, payload: AcademicYearUpdate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))
):
    year = await AcademicYearService().update_year(current_user, year_id, payload)
    return success_response(data=year, message="Academic year updated successfully")


@years_router.delete("/{year_id}", response_model=None)
async def delete_academic_year(year_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    await AcademicYearService().delete_year(current_user, year_id)
    return success_response(data=None, message="Academic year deleted successfully")


@years_router.post("/{year_id}/restore", response_model=None)
async def restore_academic_year(year_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    year = await AcademicYearService().restore_year(current_user, year_id)
    return success_response(data=year, message="Academic year restored successfully")


# --- Semesters (institution-wide -> Super Admin manages, everyone reads) ---

semesters_router = APIRouter(prefix="/semesters")


@semesters_router.get("", response_model=None)
async def list_semesters(
    academic_year_id: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await SemesterService().list_semesters(pagination, academic_year_id, include_inactive)
    return success_response(data=items, meta=meta, message="Semesters retrieved successfully")


@semesters_router.get("/lookup", response_model=None)
async def lookup_semesters(current_user: dict = Depends(get_current_user)):
    items = await SemesterService().list_all_active()
    return success_response(data=items, message="Semesters retrieved successfully")


@semesters_router.get("/{semester_id}", response_model=None)
async def get_semester(semester_id: str, current_user: dict = Depends(get_current_user)):
    semester = await SemesterService().get_semester(semester_id)
    return success_response(data=semester, message="Semester retrieved successfully")


@semesters_router.post("", response_model=None, status_code=201)
async def create_semester(payload: SemesterCreate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    semester = await SemesterService().create_semester(current_user, payload)
    return success_response(data=semester, message="Semester created successfully")


@semesters_router.patch("/{semester_id}", response_model=None)
async def update_semester(
    semester_id: str, payload: SemesterUpdate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))
):
    semester = await SemesterService().update_semester(current_user, semester_id, payload)
    return success_response(data=semester, message="Semester updated successfully")


@semesters_router.delete("/{semester_id}", response_model=None)
async def delete_semester(semester_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    await SemesterService().delete_semester(current_user, semester_id)
    return success_response(data=None, message="Semester deleted successfully")


@semesters_router.post("/{semester_id}/restore", response_model=None)
async def restore_semester(semester_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    semester = await SemesterService().restore_semester(current_user, semester_id)
    return success_response(data=semester, message="Semester restored successfully")


# --- Time Slots (Super Admin manages global slots, HOD manages their own department's) ---

timeslots_router = APIRouter(prefix="/timeslots")


@timeslots_router.get("", response_model=None)
async def list_timeslots(
    department_id: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await TimeSlotService().list_slots(current_user, pagination, department_id, include_inactive)
    return success_response(data=items, meta=meta, message="Time slots retrieved successfully")


@timeslots_router.get("/{slot_id}", response_model=None)
async def get_timeslot(slot_id: str, current_user: dict = Depends(get_current_user)):
    slot = await TimeSlotService().get_slot(slot_id)
    return success_response(data=slot, message="Time slot retrieved successfully")


@timeslots_router.post("", response_model=None, status_code=201)
async def create_timeslot(
    payload: TimeSlotCreate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HOD))
):
    slot = await TimeSlotService().create_slot(current_user, payload)
    return success_response(data=slot, message="Time slot created successfully")


@timeslots_router.patch("/{slot_id}", response_model=None)
async def update_timeslot(
    slot_id: str,
    payload: TimeSlotUpdate,
    current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HOD)),
):
    slot = await TimeSlotService().update_slot(current_user, slot_id, payload)
    return success_response(data=slot, message="Time slot updated successfully")


@timeslots_router.delete("/{slot_id}", response_model=None)
async def delete_timeslot(
    slot_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HOD))
):
    await TimeSlotService().delete_slot(current_user, slot_id)
    return success_response(data=None, message="Time slot deleted successfully")


@timeslots_router.post("/{slot_id}/restore", response_model=None)
async def restore_timeslot(
    slot_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HOD))
):
    slot = await TimeSlotService().restore_slot(current_user, slot_id)
    return success_response(data=slot, message="Time slot restored successfully")


router.include_router(years_router)
router.include_router(semesters_router)
router.include_router(timeslots_router)
