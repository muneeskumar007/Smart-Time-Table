import pytest
from pydantic import ValidationError

from app.schemas.lab import LabCreate
from app.schemas.subject_allocation import SubjectAllocationCreate


class TestLabCreate:
    def test_accepts_valid_payload(self):
        lab = LabCreate(lab_name="Computer Lab 1", room_number="cl-1", capacity=40, department_id="dept1")
        assert lab.room_number == "CL-1"

    def test_rejects_zero_capacity(self):
        with pytest.raises(ValidationError):
            LabCreate(lab_name="Computer Lab 1", room_number="CL-1", capacity=0, department_id="dept1")

    def test_rejects_capacity_above_max(self):
        with pytest.raises(ValidationError):
            LabCreate(lab_name="Computer Lab 1", room_number="CL-1", capacity=301, department_id="dept1")

    def test_rejects_missing_department(self):
        with pytest.raises(ValidationError):
            LabCreate(lab_name="Computer Lab 1", room_number="CL-1", capacity=40)

    def test_available_systems_is_optional(self):
        lab = LabCreate(lab_name="Computer Lab 1", room_number="CL-1", capacity=40, department_id="dept1")
        assert lab.available_systems is None

    def test_rejects_negative_available_systems(self):
        with pytest.raises(ValidationError):
            LabCreate(lab_name="Computer Lab 1", room_number="CL-1", capacity=40, department_id="dept1", available_systems=-1)


class TestSubjectAllocationCreate:
    def test_accepts_valid_payload(self):
        allocation = SubjectAllocationCreate(subject_id="sub1", section_id="sec1", faculty_id="fac1")
        assert allocation.subject_id == "sub1"

    def test_rejects_missing_subject_id(self):
        with pytest.raises(ValidationError):
            SubjectAllocationCreate(section_id="sec1", faculty_id="fac1")

    def test_rejects_missing_faculty_id(self):
        with pytest.raises(ValidationError):
            SubjectAllocationCreate(subject_id="sub1", section_id="sec1")
