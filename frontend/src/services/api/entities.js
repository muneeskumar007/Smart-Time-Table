import apiClient from "./axiosClient";
import { createCrudApi } from "./apiFactory";

export const departmentApi = createCrudApi("/departments");
export const userApi = createCrudApi("/users");
export const facultyApi = createCrudApi("/faculty");
export const courseApi = createCrudApi("/courses");
export const subjectApi = createCrudApi("/subjects");
export const sectionApi = createCrudApi("/sections");
export const roomApi = createCrudApi("/rooms");
export const labApi = createCrudApi("/labs");
export const academicYearApi = createCrudApi("/academic-years");
export const semesterApi = createCrudApi("/semesters");
export const timeslotApi = createCrudApi("/timeslots");

// User Management has one endpoint beyond standard CRUD (admin password reset):
userApi.resetPassword = (id, newPassword) =>
  apiClient.post(`/users/${id}/reset-password`, { new_password: newPassword }).then((res) => res.data);
