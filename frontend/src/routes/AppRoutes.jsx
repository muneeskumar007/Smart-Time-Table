import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { AuthLayout } from "../layouts/AuthLayout";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { RequireAuth, RequireRole, RedirectIfAuthenticated } from "./ProtectedRoute";
import { ROLES } from "../constants";

import LoginPage from "../pages/auth/LoginPage";
import PasswordHelpPage from "../pages/auth/PasswordHelpPage";
import DashboardPage from "../pages/dashboard/DashboardPage";
import ProfilePage from "../pages/profile/ProfilePage";
import SettingsPage from "../pages/settings/SettingsPage";
import DepartmentsPage from "../pages/departments/DepartmentsPage";
import UsersPage from "../pages/users/UsersPage";
import FacultyPage from "../pages/faculty/FacultyPage";
import CoursesPage from "../pages/courses/CoursesPage";
import SubjectsPage from "../pages/subjects/SubjectsPage";
import SectionsPage from "../pages/sections/SectionsPage";
import RoomsPage from "../pages/rooms/RoomsPage";
import LabsPage from "../pages/labs/LabsPage";
import AcademicYearsPage from "../pages/academic-years/AcademicYearsPage";
import SemestersPage from "../pages/semesters/SemestersPage";
import TimeSlotsPage from "../pages/timeslots/TimeSlotsPage";
import NotFoundPage from "../pages/system/NotFoundPage";
import UnauthorizedPage from "../pages/system/UnauthorizedPage";

const MANAGER_ROLES = [ROLES.SUPER_ADMIN, ROLES.HOD];
const ADMIN_ONLY = [ROLES.SUPER_ADMIN];

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RedirectIfAuthenticated />}>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/help/password" element={<PasswordHelpPage />} />
          </Route>
        </Route>

        <Route element={<RequireAuth />}>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />

            <Route element={<RequireRole roles={ADMIN_ONLY} />}>
              <Route path="/departments" element={<DepartmentsPage />} />
              <Route path="/rooms" element={<RoomsPage />} />
              <Route path="/academic-years" element={<AcademicYearsPage />} />
              <Route path="/semesters" element={<SemestersPage />} />
            </Route>

            <Route element={<RequireRole roles={MANAGER_ROLES} />}>
              <Route path="/users" element={<UsersPage />} />
              <Route path="/faculty" element={<FacultyPage />} />
              <Route path="/courses" element={<CoursesPage />} />
              <Route path="/subjects" element={<SubjectsPage />} />
              <Route path="/sections" element={<SectionsPage />} />
              <Route path="/labs" element={<LabsPage />} />
              <Route path="/timeslots" element={<TimeSlotsPage />} />
            </Route>

            <Route path="/unauthorized" element={<UnauthorizedPage />} />
          </Route>
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
