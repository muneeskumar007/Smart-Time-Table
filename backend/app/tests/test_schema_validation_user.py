import pytest
from pydantic import ValidationError

from app.schemas.user import ChangePasswordRequest, UserCreate


def _valid(**overrides):
    base = dict(name="Priya Sharma", email="priya@college.edu", password="Passw0rd", role="hod", department_id="dept1")
    base.update(overrides)
    return UserCreate(**base)


class TestUserCreatePasswordStrength:
    def test_accepts_valid_password(self):
        user = _valid(password="Passw0rd")
        assert user.password == "Passw0rd"

    def test_rejects_password_too_short(self):
        with pytest.raises(ValidationError, match="at least 8 characters"):
            _valid(password="Pw1")

    def test_rejects_password_without_a_letter(self):
        with pytest.raises(ValidationError, match="at least one letter"):
            _valid(password="12345678")

    def test_rejects_password_without_a_number(self):
        with pytest.raises(ValidationError, match="at least one number"):
            _valid(password="Password")


class TestUserCreateRoleRequirements:
    def test_hod_requires_department(self):
        with pytest.raises(ValidationError, match="department is required"):
            UserCreate(name="Priya Sharma", email="priya@college.edu", password="Passw0rd", role="hod", department_id=None)

    def test_faculty_requires_department(self):
        with pytest.raises(ValidationError, match="department is required"):
            UserCreate(name="A Faculty", email="f@college.edu", password="Passw0rd", role="faculty", department_id=None)

    def test_student_requires_department(self):
        with pytest.raises(ValidationError, match="department is required"):
            UserCreate(name="A Student", email="s@college.edu", password="Passw0rd", role="student", department_id=None)

    def test_super_admin_must_not_have_a_department(self):
        with pytest.raises(ValidationError, match="must not be assigned to a department"):
            UserCreate(
                name="Admin User", email="admin@college.edu", password="Passw0rd", role="super_admin", department_id="dept1"
            )

    def test_super_admin_with_no_department_is_valid(self):
        user = UserCreate(name="Admin User", email="admin@college.edu", password="Passw0rd", role="super_admin")
        assert user.department_id is None

    def test_section_id_only_allowed_for_students(self):
        with pytest.raises(ValidationError, match="Only Student accounts may be assigned to a section"):
            _valid(role="faculty", section_id="sec1")

    def test_student_may_have_a_section(self):
        user = UserCreate(
            name="A Student", email="s@college.edu", password="Passw0rd", role="student", department_id="dept1", section_id="sec1"
        )
        assert user.section_id == "sec1"


class TestChangePasswordRequest:
    def test_rejects_weak_new_password(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(current_password="whatever", new_password="weak")

    def test_accepts_strong_new_password(self):
        req = ChangePasswordRequest(current_password="whatever", new_password="NewPass123")
        assert req.new_password == "NewPass123"
