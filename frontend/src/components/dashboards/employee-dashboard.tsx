"use client";

import { CalendarDays, ClipboardList, Clock } from "lucide-react";
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
import { Button } from "@/components/ui/button";
import { listAttendance } from "@/lib/api/attendance";
import { getMyEmployeeProfile } from "@/lib/api/employees";
import { listLeaveRequests } from "@/lib/api/leave";
import { listTasks } from "@/lib/api/tasks";
import { useAuth } from "@/hooks/use-auth";
import { formatDate, todayIso } from "@/lib/format";

export function EmployeeDashboard() {
  const { user } = useAuth();

  const profileQuery = useQuery({
    queryKey: ["my-profile"],
    queryFn: getMyEmployeeProfile,
  });
  const attendanceQuery = useQuery({
    queryKey: ["attendance", { from: todayIso(), to: todayIso() }],
    queryFn: () =>
      listAttendance({ fromDate: todayIso(), toDate: todayIso() }),
  });
  const leaveQuery = useQuery({
    queryKey: ["leave-requests"],
    queryFn: () => listLeaveRequests(1, 100),
  });
  const tasksQuery = useQuery({
    queryKey: ["tasks"],
    queryFn: () => listTasks(1, 100),
  });

  const error =
    profileQuery.error ??
    attendanceQuery.error ??
    leaveQuery.error ??
    tasksQuery.error;

  if (error) {
    return <ErrorState message={(error as Error).message} />;
  }

  if (
    profileQuery.isLoading ||
    attendanceQuery.isLoading ||
    leaveQuery.isLoading ||
    tasksQuery.isLoading
  ) {
    return <LoadingState rows={4} />;
  }

  const profile = profileQuery.data;
  const today = attendanceQuery.data?.items[0];
  const pending = (leaveQuery.data?.items ?? []).filter(
    (r) => r.status === "PENDING"
  );
  const myTasks = (tasksQuery.data?.items ?? []).filter(
    (t) => t.assigned_to === profile?.id
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Hello, ${profile?.first_name ?? user?.email}`}
        description={profile ? `${profile.job_title ?? "Employee"} · ${profile.department_name ?? "No department"}` : undefined}
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Today's Status"
          value={today ? today.status.replace(/_/g, " ").toLowerCase() : "—"}
          icon={Clock}
        />
        <StatCard
          label="Hours Today"
          value={today?.hours_worked ? `${today.hours_worked} h` : "—"}
          icon={Clock}
        />
        <StatCard
          label="My Tasks"
          value={myTasks.length}
          icon={ClipboardList}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">My Pending Leave</CardTitle>
            <Button asChild variant="ghost" size="sm">
              <Link href="/leave">View all</Link>
            </Button>
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
                    <TableHead>From</TableHead>
                    <TableHead>To</TableHead>
                    <TableHead>Days</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pending.map((r) => (
                    <TableRow key={r.id}>
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

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">My Tasks</CardTitle>
            <Button asChild variant="ghost" size="sm">
              <Link href="/tasks">View all</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {myTasks.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No tasks assigned to you.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {myTasks.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell>
                        <Link href="/tasks" className="hover:underline">
                          {t.title}
                        </Link>
                      </TableCell>
                      <TableCell>{t.project_name}</TableCell>
                      <TableCell>
                        <StatusBadge status={t.priority} />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={t.status} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <CalendarDays className="h-4 w-4" />
        {formatDate(todayIso())} · {today ? "Checked in" : "Not checked in yet"} —{" "}
        <Link href="/attendance" className="text-primary hover:underline">
          go to attendance
        </Link>
      </div>
    </div>
  );
}
