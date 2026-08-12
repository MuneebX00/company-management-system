"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState, EmptyState } from "@/components/data-state";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listDepartments } from "@/lib/api/departments";
import { listEmployers } from "@/lib/api/employers";
import {
  createEmployee,
  listEmployees,
  updateEmployee,
} from "@/lib/api/employees";
import { listUsers } from "@/lib/api/users";
import { getErrorMessage } from "@/lib/api/client";
import { useAuth } from "@/hooks/use-auth";
import { EMPLOYMENT_STATUSES, type Employee } from "@/lib/types";

const employeeSchema = z.object({
  userId: z.string().min(1, "Select a user"),
  departmentId: z.string().optional(),
  employerId: z.string().optional(),
  employeeNumber: z.string().min(1, "Employee number is required"),
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  jobTitle: z.string().optional(),
  hireDate: z.string().optional(),
  employmentStatus: z.string().min(1, "Status is required"),
  phone: z.string().optional(),
});

type EmployeeFormValues = z.infer<typeof employeeSchema>;

export default function EmployeesPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN_HR";
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);

  const employeesQuery = useQuery({
    queryKey: ["employees"],
    queryFn: () => listEmployees(1, 100),
  });
  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: () => listUsers(1, 100),
    enabled: isAdmin,
  });
  const departmentsQuery = useQuery({
    queryKey: ["departments"],
    queryFn: () => listDepartments(1, 100),
    enabled: isAdmin,
  });
  const employersQuery = useQuery({
    queryKey: ["employers"],
    queryFn: () => listEmployers(1, 100),
    enabled: isAdmin,
  });

  const form = useForm<EmployeeFormValues>({
    resolver: zodResolver(employeeSchema),
    defaultValues: {
      userId: "",
      departmentId: "",
      employerId: "",
      employeeNumber: "",
      firstName: "",
      lastName: "",
      jobTitle: "",
      hireDate: "",
      employmentStatus: "ACTIVE",
      phone: "",
    },
  });

  useEffect(() => {
    if (!dialogOpen) return;
    if (editing) {
      form.reset({
        userId: editing.user_id,
        departmentId: editing.department_id ?? "",
        employerId: editing.employer_id ?? "",
        employeeNumber: editing.employee_number,
        firstName: editing.first_name,
        lastName: editing.last_name,
        jobTitle: editing.job_title ?? "",
        hireDate: editing.hire_date ?? "",
        employmentStatus: editing.employment_status,
        phone: editing.phone ?? "",
      });
    } else {
      form.reset({
        userId: "",
        departmentId: "",
        employerId: "",
        employeeNumber: "",
        firstName: "",
        lastName: "",
        jobTitle: "",
        hireDate: "",
        employmentStatus: "ACTIVE",
        phone: "",
      });
    }
  }, [dialogOpen, editing, form]);

  const saveMutation = useMutation({
    mutationFn: (values: EmployeeFormValues) => {
      const payload = {
        department_id: values.departmentId || null,
        employer_id: values.employerId || null,
        employee_number: values.employeeNumber,
        first_name: values.firstName,
        last_name: values.lastName,
        job_title: values.jobTitle || null,
        hire_date: values.hireDate || null,
        employment_status: values.employmentStatus as Employee["employment_status"],
        phone: values.phone || null,
      };
      return editing
        ? updateEmployee(editing.id, payload)
        : createEmployee({ user_id: values.userId, ...payload });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employees"] });
      toast.success(editing ? "Employee updated" : "Employee created");
      setDialogOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to save employee"));
    },
  });

  const employees = employeesQuery.data?.items ?? [];
  const existingIds = new Set(employees.map((e) => e.user_id));
  const employeeUsers =
    usersQuery.data?.items.filter(
      (u) => u.role === "EMPLOYEE" && !existingIds.has(u.id)
    ) ?? [];
  const departments = departmentsQuery.data?.items ?? [];
  const employers = employersQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Employees"
        description={
          isAdmin
            ? "Manage employee profiles in your company."
            : "View employees in your team."
        }
        actions={
          isAdmin ? (
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              Add employee
            </Button>
          ) : undefined
        }
      />

      {employeesQuery.isLoading ? (
        <LoadingState rows={4} />
      ) : employeesQuery.isError ? (
        <ErrorState message={(employeesQuery.error as Error).message} />
      ) : employees.length === 0 ? (
        <EmptyState
          title="No employees yet"
          description={
            isAdmin
              ? "Create an employee profile for an EMPLOYEE user."
              : "No employees found."
          }
          action={
            isAdmin ? (
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4" />
                Add employee
              </Button>
            ) : undefined
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All employees</CardTitle>
            <CardDescription>
              {employeesQuery.data?.total ?? 0} employee(s) in total.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Manager</TableHead>
                  <TableHead>Job title</TableHead>
                  <TableHead>Status</TableHead>
                  {isAdmin ? (
                    <TableHead className="text-right">Actions</TableHead>
                  ) : null}
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((employee) => (
                  <TableRow key={employee.id}>
                    <TableCell className="font-medium">
                      {employee.first_name} {employee.last_name}
                    </TableCell>
                    <TableCell>{employee.email}</TableCell>
                    <TableCell>{employee.department_name ?? "—"}</TableCell>
                    <TableCell>{employee.manager_name ?? "—"}</TableCell>
                    <TableCell>{employee.job_title ?? "—"}</TableCell>
                    <TableCell>
                      <StatusBadge status={employee.employment_status} />
                    </TableCell>
                    {isAdmin ? (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            setEditing(employee);
                            setDialogOpen(true);
                          }}
                          aria-label={`Edit ${employee.first_name}`}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editing ? "Edit employee" : "Add employee"}
            </DialogTitle>
            <DialogDescription>
              {editing
                ? "Update the employee profile details."
                : "Create an employee profile for an existing EMPLOYEE user."}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))}
            className="space-y-4"
            noValidate
          >
            {!editing ? (
              <div className="space-y-1.5">
                <Label htmlFor="userId">User</Label>
                <Select
                  value={form.watch("userId")}
                  onValueChange={(value) => form.setValue("userId", value)}
                >
                  <SelectTrigger id="userId">
                    <SelectValue placeholder="Select an EMPLOYEE user" />
                  </SelectTrigger>
                  <SelectContent>
                    {employeeUsers.length === 0 ? (
                      <SelectItem value="__none" disabled>
                        No available users
                      </SelectItem>
                    ) : (
                      employeeUsers.map((user) => (
                        <SelectItem key={user.id} value={user.id}>
                          {user.email}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                {form.formState.errors.userId ? (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.userId.message}
                  </p>
                ) : null}
                {employeeUsers.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    No EMPLOYEE users available. Register a user with the
                    EMPLOYEE role first.
                  </p>
                ) : null}
              </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="firstName">First name</Label>
                <Input id="firstName" {...form.register("firstName")} />
                {form.formState.errors.firstName ? (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.firstName.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="lastName">Last name</Label>
                <Input id="lastName" {...form.register("lastName")} />
                {form.formState.errors.lastName ? (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.lastName.message}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="employeeNumber">Employee number</Label>
                <Input id="employeeNumber" {...form.register("employeeNumber")} />
                {form.formState.errors.employeeNumber ? (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.employeeNumber.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="jobTitle">Job title</Label>
                <Input id="jobTitle" {...form.register("jobTitle")} />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="departmentId">Department</Label>
                <Select
                  value={form.watch("departmentId") ?? ""}
                  onValueChange={(value) =>
                    form.setValue("departmentId", value === "__none" ? "" : value)
                  }
                >
                  <SelectTrigger id="departmentId">
                    <SelectValue placeholder="No department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none">No department</SelectItem>
                    {departments.map((department) => (
                      <SelectItem key={department.id} value={department.id}>
                        {department.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="employerId">Manager (employer)</Label>
                <Select
                  value={form.watch("employerId") ?? ""}
                  onValueChange={(value) =>
                    form.setValue("employerId", value === "__none" ? "" : value)
                  }
                >
                  <SelectTrigger id="employerId">
                    <SelectValue placeholder="No manager" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none">No manager</SelectItem>
                    {employers.map((employer) => (
                      <SelectItem key={employer.id} value={employer.id}>
                        {employer.first_name} {employer.last_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="employmentStatus">Employment status</Label>
                <Select
                  value={form.watch("employmentStatus")}
                  onValueChange={(value) =>
                    form.setValue("employmentStatus", value)
                  }
                >
                  <SelectTrigger id="employmentStatus">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EMPLOYMENT_STATUSES.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status.replace(/_/g, " ")}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {form.formState.errors.employmentStatus ? (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.employmentStatus.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="hireDate">Hire date</Label>
                <Input id="hireDate" type="date" {...form.register("hireDate")} />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" {...form.register("phone")} />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogOpen(false)}
                disabled={saveMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? "Saving…" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
