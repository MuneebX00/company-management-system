"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import Link from "next/link";
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
import { Textarea } from "@/components/ui/textarea";
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
  createProject,
  deleteProject,
  listProjects,
} from "@/lib/api/projects";
import { listEmployers } from "@/lib/api/employers";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import type { Project } from "@/lib/types";

const projectSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  ownerId: z.string().optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

export default function ProjectsPage() {
  const { user } = useAuth();
  const canManage = user?.role === "ADMIN_HR" || user?.role === "EMPLOYER";
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState<Project | null>(null);

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects(1, 100),
  });
  const employersQuery = useQuery({
    queryKey: ["employers"],
    queryFn: () => listEmployers(1, 100),
    enabled: canManage,
  });

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      description: "",
      ownerId: "",
      startDate: "",
      endDate: "",
    },
  });

  useEffect(() => {
    if (dialogOpen) {
      form.reset({
        name: "",
        description: "",
        ownerId: "",
        startDate: "",
        endDate: "",
      });
    }
  }, [dialogOpen, form]);

  const createMutation = useMutation({
    mutationFn: (values: ProjectFormValues) =>
      createProject({
        name: values.name,
        description: values.description || null,
        owner_id: values.ownerId || null,
        start_date: values.startDate || null,
        end_date: values.endDate || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project created");
      setDialogOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to create project"));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project deleted");
      setDeleting(null);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to delete project"));
    },
  });

  const projects = projectsQuery.data?.items ?? [];
  const employers = employersQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Track projects across your company."
        actions={
          canManage ? (
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              New project
            </Button>
          ) : undefined
        }
      />

      {projectsQuery.isLoading ? (
        <LoadingState rows={4} />
      ) : projectsQuery.isError ? (
        <ErrorState message={(projectsQuery.error as Error).message} />
      ) : projects.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Projects will appear here once created."
          action={
            canManage ? (
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4" />
                New project
              </Button>
            ) : undefined
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All projects</CardTitle>
            <CardDescription>
              {projectsQuery.data?.total ?? 0} project(s).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Members</TableHead>
                  <TableHead>Start</TableHead>
                  <TableHead>End</TableHead>
                  {canManage ? (
                    <TableHead className="text-right">Actions</TableHead>
                  ) : null}
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((project) => (
                  <TableRow key={project.id}>
                    <TableCell className="font-medium">
                      <Link
                        href={`/projects/${project.id}`}
                        className="hover:underline"
                      >
                        {project.name}
                      </Link>
                    </TableCell>
                    <TableCell>{project.owner_name ?? "—"}</TableCell>
                    <TableCell>
                      <StatusBadge status={project.status} />
                    </TableCell>
                    <TableCell>{project.member_count}</TableCell>
                    <TableCell>{formatDate(project.start_date)}</TableCell>
                    <TableCell>{formatDate(project.end_date)}</TableCell>
                    {canManage ? (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleting(project)}
                          aria-label={`Delete ${project.name}`}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
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
            <DialogTitle>New project</DialogTitle>
            <DialogDescription>Create a new project.</DialogDescription>
          </DialogHeader>
          <form
            onSubmit={form.handleSubmit((v) => createMutation.mutate(v))}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" {...form.register("name")} />
              {form.formState.errors.name ? (
                <p className="text-xs text-destructive">
                  {form.formState.errors.name.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                rows={3}
                {...form.register("description")}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ownerId">Owner (employer)</Label>
              <Select
                value={form.watch("ownerId") ?? ""}
                onValueChange={(value) =>
                  form.setValue("ownerId", value === "__none" ? "" : value)
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
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="startDate">Start date</Label>
                <Input
                  id="startDate"
                  type="date"
                  {...form.register("startDate")}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="endDate">End date</Label>
                <Input id="endDate" type="date" {...form.register("endDate")} />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogOpen(false)}
                disabled={createMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating…" : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => {
          if (!open) setDeleting(null);
        }}
        title="Delete project"
        description={`Are you sure you want to delete "${deleting?.name}"? Its tasks and members will also be removed. This cannot be undone.`}
        confirmLabel="Delete"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => {
          if (deleting) deleteMutation.mutate(deleting.id);
        }}
      />
    </div>
  );
}
