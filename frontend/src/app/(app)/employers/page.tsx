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
import {
  createEmployer,
  listEmployers,
  updateEmployer,
} from "@/lib/api/employers";
import { listUsers } from "@/lib/api/users";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate } from "@/lib/format";
import type { Employer } from "@/lib/types";

const employerSchema = z.object({
  userId: z.string().min(1, "Select a user"),
  departmentId: z.string().optional(),
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  jobTitle: z.string().optional(),
  hireDate: z.string().optional(),
});

type EmployerFormValues = z.infer<typeof employerSchema>;

export default function EmployersPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Employer | null>(null);

  const employersQuery = useQuery({
    queryKey: ["employers"],
    queryFn: () => listEmployers(1, 100),
  });
  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: () => listUsers(1, 100),
  });
  const departmentsQuery = useQuery({
    queryKey: ["departments"],
    queryFn: () => listDepartments(1, 100),
  });

  const form = useForm<EmployerFormValues>({
    resolver: zodResolver(employerSchema),
    defaultValues: {
      userId: "",
      departmentId: "",
      firstName: "",
      lastName: "",
      jobTitle: "",
      hireDate: "",
    },
  });

  useEffect(() => {
    if (!dialogOpen) return;
    if (editing) {
      form.reset({
        userId: editing.user_id,
        departmentId: editing.department_id ?? "",
        firstName: editing.first_name,
        lastName: editing.last_name,
        jobTitle: editing.job_title ?? "",
        hireDate: editing.hire_date ?? "",
      });
    } else {
      form.reset({
        userId: "",
        departmentId: "",
        firstName: "",
        lastName: "",
        jobTitle: "",
        hireDate: "",
      });
    }
  }, [dialogOpen, editing, form]);

  const saveMutation = useMutation({
    mutationFn: (values: EmployerFormValues) => {
      const payload = {
        department_id: values.departmentId || null,
        first_name: values.firstName,
        last_name: values.lastName,
        job_title: values.jobTitle || null,
        hire_date: values.hireDate || null,
      };
      return editing
        ? updateEmployer(editing.id, payload)
        : createEmployer({ user_id: values.userId, ...payload });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employers"] });
      toast.success(editing ? "Employer updated" : "Employer created");
      setDialogOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to save employer"));
    },
  });

  const employers = employersQuery.data?.items ?? [];
  const existingIds = new Set(employers.map((e) => e.user_id));
  const employerUsers =
    usersQuery.data?.items.filter(
      (u) => u.role === "EMPLOYER" && !existingIds.has(u.id)
    ) ?? [];
  const departments = departmentsQuery.data?.items ?? [];

  const isLoading =
    employersQuery.isLoading ||
    usersQuery.isLoading ||
    departmentsQuery.isLoading;
  const error =
    employersQuery.error ?? usersQuery.error ?? departmentsQuery.error;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Employers"
        description="Manage employer profiles in your company."
        actions={
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4" />
            Add employer
          </Button>
        }
      />

      {isLoading ? (
        <LoadingState rows={4} />
      ) : error ? (
        <ErrorState message={(error as Error).message} />
      ) : employers.length === 0 ? (
        <EmptyState
          title="No employers yet"
          description="Create an employer profile for an EMPLOYER user."
          action={
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              Add employer
            </Button>
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All employers</CardTitle>
            <CardDescription>
              {employersQuery.data?.total ?? 0} employer(s) in total.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Job title</TableHead>
                  <TableHead>Hire date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employers.map((employer) => (
                  <TableRow key={employer.id}>
                    <TableCell className="font-medium">
                      {employer.first_name} {employer.last_name}
                    </TableCell>
                    <TableCell>{employer.email}</TableCell>
                    <TableCell>{employer.department_name ?? "—"}</TableCell>
                    <TableCell>{employer.job_title ?? "—"}</TableCell>
                    <TableCell>{formatDate(employer.hire_date)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          setEditing(employer);
                          setDialogOpen(true);
                        }}
                        aria-label={`Edit ${employer.first_name}`}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </TableCell>
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
              {editing ? "Edit employer" : "Add employer"}
            </DialogTitle>
            <DialogDescription>
              {editing
                ? "Update the employer profile details."
                : "Create an employer profile for an existing EMPLOYER user."}
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
                    <SelectValue placeholder="Select an EMPLOYER user" />
                  </SelectTrigger>
                  <SelectContent>
                    {employerUsers.length === 0 ? (
                      <SelectItem value="__none" disabled>
                        No available users
                      </SelectItem>
                    ) : (
                      employerUsers.map((user) => (
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
                {employerUsers.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    No EMPLOYER users available. Register a user with the
                    EMPLOYER role first.
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

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="jobTitle">Job title</Label>
                <Input id="jobTitle" {...form.register("jobTitle")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="hireDate">Hire date</Label>
                <Input id="hireDate" type="date" {...form.register("hireDate")} />
              </div>
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
