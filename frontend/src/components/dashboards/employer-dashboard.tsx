"use client";

import { CalendarDays, ClipboardList, Users } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { ErrorState, LoadingState } from "@/components/data-state";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { listEmployees } from "@/lib/api/employees";
import { listLeaveRequests } from "@/lib/api/leave";
import { listProjects } from "@/lib/api/projects";
import { useAuth } from "@/hooks/use-auth";
import { formatDate } from "@/lib/format";

export function EmployerDashboard() {
  const { user } = useAuth();

  const employeesQuery = useQuery({
    queryKey: ["employees"],
    queryFn: () => listEmployees(1, 100),
  });
  const leaveQuery = useQuery({
    queryKey: ["leave-requests"],
    queryFn: () => listLeaveRequests(1, 100),
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects(1, 100),
  });

  const error =
    employeesQuery.error ?? leaveQuery.error ?? projectsQuery.error;

  if (error) {
    return <ErrorState message={(error as Error).message} />;
  }

  if (
    employeesQuery.isLoading ||
    leaveQuery.isLoading ||
    projectsQuery.isLoading
  ) {
    return <LoadingState rows={4} />;
  }

  const pending = (leaveQuery.data?.items ?? []).filter(
    (r) => r.status === "PENDING"
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description={
          user?.company_name ? `Welcome back, ${user?.email}` : undefined
        }
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Employees"
          value={employeesQuery.data?.total ?? 0}
          icon={Users}
        />
        <StatCard
          label="Projects"
          value={projectsQuery.data?.total ?? 0}
          icon={ClipboardList}
        />
        <StatCard
          label="Pending Leave"
          value={pending.length}
          icon={CalendarDays}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pending Leave Requests</CardTitle>
        </CardHeader>
        <CardContent>
          {pending.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              No pending leave requests.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                  <TableHead>Days</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pending.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>
                      <Link href="/leave" className="hover:underline">
                        {r.employee_name}
                      </Link>
                    </TableCell>
                    <TableCell>{r.leave_type_name}</TableCell>
                    <TableCell>{formatDate(r.start_date)}</TableCell>
                    <TableCell>{formatDate(r.end_date)}</TableCell>
                    <TableCell>{r.days}</TableCell>
                    <TableCell>
                      <StatusBadge status={r.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
