"use client";

import { useQuery } from "@tanstack/react-query";
import { Building2, Mail, UserRound } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { LoadingState } from "@/components/data-state";
import { StatusBadge } from "@/components/status-badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getMyEmployeeProfile } from "@/lib/api/employees";
import { useAuth } from "@/hooks/use-auth";
import { formatDate, formatDateTime } from "@/lib/format";

export default function ProfilePage() {
  const { user } = useAuth();

  const profileQuery = useQuery({
    queryKey: ["my-profile"],
    queryFn: getMyEmployeeProfile,
    retry: false,
  });

  const hasEmployeeProfile =
    !profileQuery.isError && profileQuery.data !== undefined;

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Your account details." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
            <CardDescription>Your login and role information.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">{user?.email}</span>
            </div>
            <div className="flex items-center gap-3">
              <UserRound className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">
                Role: <span className="font-medium">{user?.role}</span>
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">
                Company:{" "}
                <span className="font-medium">{user?.company_name}</span>
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                Last login:{" "}
                <span className="text-foreground">
                  {formatDateTime(user?.last_login_at)}
                </span>
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                Status:{" "}
                <StatusBadge status={user?.is_active ? "ACTIVE" : "TERMINATED"} />
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Employee profile</CardTitle>
            <CardDescription>
              {hasEmployeeProfile
                ? "Your employee record."
                : "No employee profile is linked to this account."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {profileQuery.isLoading ? (
              <LoadingState rows={3} />
            ) : !hasEmployeeProfile ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Contact an administrator if you believe this is a mistake.
              </p>
            ) : (
              (() => {
                const profile = profileQuery.data;
                return (
                  <dl className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <dt className="text-sm font-medium">Name</dt>
                      <dd className="text-sm text-muted-foreground">
                        {profile.first_name} {profile.last_name}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium">Employee number</dt>
                      <dd className="text-sm text-muted-foreground">
                        {profile.employee_number}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium">Department</dt>
                      <dd className="text-sm text-muted-foreground">
                        {profile.department_name ?? "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium">Job title</dt>
                      <dd className="text-sm text-muted-foreground">
                        {profile.job_title ?? "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium">Manager</dt>
                      <dd className="text-sm text-muted-foreground">
                        {profile.manager_name ?? "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium">Hire date</dt>
                      <dd className="text-sm text-muted-foreground">
                        {formatDate(profile.hire_date)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium">Employment status</dt>
                      <dd className="text-sm text-muted-foreground">
                        <StatusBadge status={profile.employment_status} />
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium">Phone</dt>
                      <dd className="text-sm text-muted-foreground">
                        {profile.phone ?? "—"}
                      </dd>
                    </div>
                  </dl>
                );
              })()
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
