"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Pencil, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState, EmptyState } from "@/components/data-state";
import { ConfirmDialog } from "@/components/confirm-dialog";
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
import {
  addProjectMember,
  getProject,
  listProjectMembers,
  removeProjectMember,
  updateProject,
} from "@/lib/api/projects";
import { listEmployees } from "@/lib/api/employees";
import { listEmployers } from "@/lib/api/employers";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import { PROJECT_STATUSES } from "@/lib/types";

const editSchema = z.object({
  name: z.string().min(1, "Name is required"),
  status: z.string().min(1, "Status is required"),
  ownerId: z.string().optional(),
});

type EditFormValues = z.infer<typeof editSchema>;

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const { user } = useAuth();
  const canManage = user?.role === "ADMIN_HR" || user?.role === "EMPLOYER";
  const queryClient = useQueryClient();

  const [editOpen, setEditOpen] = useState(false);
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [removing, setRemoving] = useState<{ employeeId: string; name: string } | null>(null);
  const [newMember, setNewMember] = useState("");
  const [newRole, setNewRole] = useState("");

  const projectQuery = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
    enabled: !!projectId,
  });
  const membersQuery = useQuery({
    queryKey: ["project-members", projectId],
    queryFn: () => listProjectMembers(projectId),
    enabled: !!projectId,
  });
  const employeesQuery = useQuery({
    queryKey: ["employees"],
    queryFn: () => listEmployees(1, 100),
    enabled: canManage,
  });
  const employersQuery = useQuery({
    queryKey: ["employers"],
    queryFn: () => listEmployers(1, 100),
    enabled: canManage,
  });

  const editForm = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: { name: "", status: "NOT_STARTED", ownerId: "" },
  });

  useEffect(() => {
    if (editOpen && projectQuery.data) {
      editForm.reset({
        name: projectQuery.data.name,
        status: projectQuery.data.status,
        ownerId: projectQuery.data.owner_id ?? "",
      });
    }
  }, [editOpen, projectQuery.data, editForm]);

  const updateMutation = useMutation({
    mutationFn: (values: EditFormValues) =>
      updateProject(projectId, {
        name: values.name,
        status: values.status as (typeof PROJECT_STATUSES)[number],
        owner_id: values.ownerId || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project updated");
      setEditOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to update project"));
    },
  });

  const addMemberMutation = useMutation({
    mutationFn: (values: { employeeId: string; role: string }) =>
      addProjectMember(projectId, {
        employee_id: values.employeeId,
        role: values.role || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-members", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      toast.success("Member added");
      setAddMemberOpen(false);
      setNewMember("");
      setNewRole("");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to add member"));
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: (employeeId: string) =>
      removeProjectMember(projectId, employeeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-members", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      toast.success("Member removed");
      setRemoving(null);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to remove member"));
    },
  });

  if (projectQuery.isLoading) return <LoadingState rows={3} />;
  if (projectQuery.isError) {
    return <ErrorState message={(projectQuery.error as Error).message} />;
  }
  if (!projectQuery.data) return null;

  const project = projectQuery.data;
  const members = membersQuery.data ?? [];
  const memberIds = new Set(members.map((m) => m.employee_id));
  const availableEmployees =
    employeesQuery.data?.items.filter((e) => !memberIds.has(e.id)) ?? [];
  const employers = employersQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={project.name}
        description={project.description ?? undefined}
        actions={
          <div className="flex gap-2">
            <Button asChild variant="outline" size="sm">
              <Link href="/projects">
                <ArrowLeft className="h-4 w-4" />
                All projects
              </Link>
            </Button>
            {canManage ? (
              <Button size="sm" onClick={() => setEditOpen(true)}>
                <Pencil className="h-4 w-4" />
                Edit
              </Button>
            ) : null}
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-sm text-muted-foreground">Status</p>
            <p className="mt-1">
              <StatusBadge status={project.status} />
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Owner</p>
            <p className="mt-1 text-sm font-medium">{project.owner_name ?? "—"}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Start date</p>
            <p className="mt-1 text-sm font-medium">
              {formatDate(project.start_date)}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">End date</p>
            <p className="mt-1 text-sm font-medium">{formatDate(project.end_date)}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle className="text-base">Members</CardTitle>
            <CardDescription>
              {members.length} member(s) on this project.
            </CardDescription>
          </div>
          {canManage ? (
            <Button
              size="sm"
              onClick={() => setAddMemberOpen(true)}
              disabled={availableEmployees.length === 0}
            >
              <Plus className="h-4 w-4" />
              Add member
            </Button>
          ) : null}
        </CardHeader>
        <CardContent>
          {membersQuery.isLoading ? (
            <LoadingState rows={2} />
          ) : members.length === 0 ? (
            <EmptyState
              title="No members yet"
              description="Add employees to work on this project."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Role</TableHead>
                  {canManage ? (
                    <TableHead className="text-right">Actions</TableHead>
                  ) : null}
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.employee_id}>
                    <TableCell className="font-medium">
                      {member.employee_name}
                    </TableCell>
                    <TableCell>{member.role ?? "—"}</TableCell>
                    {canManage ? (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            setRemoving({
                              employeeId: member.employee_id,
                              name: member.employee_name,
                            })
                          }
                          aria-label={`Remove ${member.employee_name}`}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit project</DialogTitle>
            <DialogDescription>Update project details.</DialogDescription>
          </DialogHeader>
          <form
            onSubmit={editForm.handleSubmit((v) => updateMutation.mutate(v))}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" {...editForm.register("name")} />
              {editForm.formState.errors.name ? (
                <p className="text-xs text-destructive">
                  {editForm.formState.errors.name.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="status">Status</Label>
              <Select
                value={editForm.watch("status")}
                onValueChange={(value) => editForm.setValue("status", value)}
              >
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PROJECT_STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status.replace(/_/g, " ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ownerId">Owner (employer)</Label>
              <Select
                value={editForm.watch("ownerId") ?? ""}
                onValueChange={(value) =>
                  editForm.setValue("ownerId", value === "__none" ? "" : value)
                }
              >
                <SelectTrigger id="ownerId">
                  <SelectValue placeholder="No owner" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none">No owner</SelectItem>
                  {employers.map((employer) => (
                    <SelectItem key={employer.id} value={employer.id}>
                      {employer.first_name} {employer.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setEditOpen(false)}
                disabled={updateMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "Saving…" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={addMemberOpen} onOpenChange={setAddMemberOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add member</DialogTitle>
            <DialogDescription>Add an employee to this project.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="employee">Employee</Label>
              <Select value={newMember} onValueChange={setNewMember}>
                <SelectTrigger id="employee">
                  <SelectValue placeholder="Select an employee" />
                </SelectTrigger>
                <SelectContent>
                  {availableEmployees.length === 0 ? (
                    <SelectItem value="__none" disabled>
                      No available employees
                    </SelectItem>
                  ) : (
                    availableEmployees.map((employee) => (
                      <SelectItem key={employee.id} value={employee.id}>
                        {employee.first_name} {employee.last_name} ({employee.email})
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="role">Role on project</Label>
              <Input
                id="role"
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
                placeholder="e.g. Developer, Tester"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAddMemberOpen(false)}
              disabled={addMemberMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={() =>
                addMemberMutation.mutate({ employeeId: newMember, role: newRole })
              }
              disabled={addMemberMutation.isPending || !newMember}
            >
              {addMemberMutation.isPending ? "Adding…" : "Add"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={removing !== null}
        onOpenChange={(open) => {
          if (!open) setRemoving(null);
        }}
        title="Remove member"
        description={`Remove ${removing?.name} from this project?`}
        confirmLabel="Remove"
        destructive
        loading={removeMemberMutation.isPending}
        onConfirm={() => {
          if (removing) removeMemberMutation.mutate(removing.employeeId);
        }}
      />
    </div>
  );
}
