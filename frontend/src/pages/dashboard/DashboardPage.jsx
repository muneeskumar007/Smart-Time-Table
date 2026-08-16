import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Building2, GraduationCap, BookOpen, Layers, DoorOpen, FlaskConical, Users, CalendarCheck, FileClock } from "lucide-react";
import { PageHeader } from "../../components/common/PageHeader";
import { Card, CardHeader, StatCard } from "../../components/common/Card";
import { EmptyState } from "../../components/common/EmptyState";
import { useAuth } from "../../context/AuthContext";
import { ROLES } from "../../constants";
import { departmentApi, facultyApi, courseApi, subjectApi, sectionApi, roomApi, labApi, userApi } from "../../services/api/entities";
import apiClient from "../../services/api/axiosClient";

const timetableApi = { list: (params) => apiClient.get("/timetable", { params }).then((res) => res.data) };
const academicYearLookup = () => apiClient.get("/academic-years/lookup").then((res) => res.data);
const semesterLookup = () => apiClient.get("/semesters/lookup").then((res) => res.data);

function useCount(key, fn, enabled = true) {
  return useQuery({
    queryKey: key,
    queryFn: fn,
    enabled,
    staleTime: 30_000,
  });
}

export default function DashboardPage() {
  const { user } = useAuth();
  const isManager = user?.role === ROLES.SUPER_ADMIN || user?.role === ROLES.HOD;

  const departments = useCount(["dash", "departments"], () => departmentApi.list({ limit: 50 }), isManager);
  const faculty = useCount(["dash", "faculty"], () => facultyApi.list({ limit: 1 }), isManager);
  const students = useCount(["dash", "students"], () => userApi.list({ role: "student", limit: 1 }), isManager);
  const courses = useCount(["dash", "courses"], () => courseApi.list({ limit: 1 }), isManager);
  const subjects = useCount(["dash", "subjects"], () => subjectApi.list({ limit: 1 }), isManager);
  const sections = useCount(["dash", "sections"], () => sectionApi.list({ limit: 1 }), isManager);
  const rooms = useCount(["dash", "rooms"], () => roomApi.list({ limit: 1 }), isManager);
  const labs = useCount(["dash", "labs"], () => labApi.list({ limit: 1 }), isManager);
  const published = useCount(["dash", "tt-published"], () => timetableApi.list({ status: "published", limit: 1 }), isManager);
  const drafts = useCount(["dash", "tt-draft"], () => timetableApi.list({ status: "draft", limit: 1 }), isManager);
  const years = useCount(["dash", "years"], academicYearLookup, isManager);
  const semesters = useCount(["dash", "semesters"], semesterLookup, isManager);

  const currentYear = years.data?.data?.find((y) => y.is_current);
  const currentSemester = semesters.data?.data?.find((s) => s.is_current);

  const chartData = (departments.data?.data ?? []).map((d) => ({
    name: d.code,
    Faculty: d.faculty_count,
    Courses: d.course_count,
    Sections: d.section_count,
  }));

  if (!isManager) {
    return <NonManagerDashboard />;
  }

  return (
    <div>
      <PageHeader title={`Welcome back, ${user?.name?.split(" ")[0]}`} subtitle="Here's what's happening across your department today." />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <StatCard label="Departments" value={departments.data?.meta?.total ?? "—"} icon={Building2} isLoading={departments.isLoading} />
        <StatCard label="Faculty" value={faculty.data?.meta?.total ?? "—"} icon={GraduationCap} accent="emerald" isLoading={faculty.isLoading} />
        <StatCard label="Students" value={students.data?.meta?.total ?? "—"} icon={Users} accent="amber" isLoading={students.isLoading} />
        <StatCard label="Courses" value={courses.data?.meta?.total ?? "—"} icon={BookOpen} isLoading={courses.isLoading} />
        <StatCard label="Subjects" value={subjects.data?.meta?.total ?? "—"} icon={Layers} accent="emerald" isLoading={subjects.isLoading} />
        <StatCard label="Classrooms" value={rooms.data?.meta?.total ?? "—"} icon={DoorOpen} isLoading={rooms.isLoading} />
        <StatCard label="Laboratories" value={labs.data?.meta?.total ?? "—"} icon={FlaskConical} accent="amber" isLoading={labs.isLoading} />
        <StatCard label="Sections" value={sections.data?.meta?.total ?? "—"} icon={Layers} isLoading={sections.isLoading} />
        <StatCard
          label="Published Timetables"
          value={published.data?.meta?.total ?? "—"}
          icon={CalendarCheck}
          accent="emerald"
          isLoading={published.isLoading}
        />
        <StatCard label="Draft Timetables" value={drafts.data?.meta?.total ?? "—"} icon={FileClock} accent="amber" isLoading={drafts.isLoading} />
        <StatCard label="Active Academic Year" value={currentYear?.name ?? "Not set"} icon={CalendarCheck} isLoading={years.isLoading} />
        <StatCard label="Active Semester" value={currentSemester?.name ?? "Not set"} icon={CalendarCheck} isLoading={semesters.isLoading} />
      </div>

      <Card className="mt-6">
        <CardHeader title="Departments overview" subtitle="Faculty, courses and sections per department" />
        {departments.isLoading ? (
          <div className="h-72 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
        ) : chartData.length === 0 ? (
          <EmptyState title="No departments yet" description="Add a department to see it charted here." />
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-slate-100 dark:text-slate-800" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate-400" />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} stroke="currentColor" className="text-slate-400" />
              <Tooltip
                contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 13 }}
                cursor={{ fill: "rgba(34,68,180,0.06)" }}
              />
              <Bar dataKey="Faculty" fill="#2244B4" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Courses" fill="#607EE1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Sections" fill="#C7D2F4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}

function NonManagerDashboard() {
  const { user } = useAuth();
  const isStudent = user?.role === ROLES.STUDENT;

  return (
    <div>
      <PageHeader title={`Welcome, ${user?.name?.split(" ")[0]}`} subtitle="Your personal overview." />
      <Card>
        <EmptyState
          icon={CalendarCheck}
          title={isStudent ? "Your timetable will appear here" : "Your teaching schedule will appear here"}
          description={
            isStudent
              ? "Once your department publishes a timetable for your section, you'll be able to view and download it here."
              : "Once your department publishes a timetable that includes your sessions, your weekly schedule and workload will appear here."
          }
        />
      </Card>
    </div>
  );
}
