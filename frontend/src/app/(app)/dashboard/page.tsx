"use client";

import { AdminDashboard } from "@/components/dashboards/admin-dashboard";
import { EmployeeDashboard } from "@/components/dashboards/employee-dashboard";
import { EmployerDashboard } from "@/components/dashboards/employer-dashboard";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user } = useAuth();

  if (user?.role === "ADMIN_HR") return <AdminDashboard />;
  if (user?.role === "EMPLOYER") return <EmployerDashboard />;
  return <EmployeeDashboard />;
}
