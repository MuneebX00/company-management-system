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
import { createTask, listTasks, updateTask } from "@/lib/api/tasks";
import { listEmployees } from "@/lib/api/employees";
import { listProjects } from "@/lib/api/projects";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import { TASK_PRIORITIES, TASK_STATUSES, type Task } from "@/lib/types";

const taskSchema = z.object({
  projectId: z.string().min(1, "Select a project"),
  title: z.string().min(1, "Title is required"),
  description: z.string().optional(),
  assignedTo: z.string().optional(),
  priority: z.string().min(1, "Priority is required"),
  dueDate: z.string().optional(),
});

type TaskFormValues = z.infer<typeof taskSchema>;

export default function TasksPage() {
  const { user } = useAuth();
  const isEmployee = user?.role === "EMPLOYEE";
  const canManage = !isEmployee;
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);

  const tasksQuery = useQuery({
    queryKey: ["tasks"],
    queryFn: () => listTasks(1, 100),
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects(1, 100),
    enabled: canManage,
  });
  const employeesQuery = useQuery({
    queryKey: ["employees"],
    queryFn: () => listEmployees(1, 100),
    enabled: canManage,
  });

  const form = useForm<TaskFormValues>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      projectId: "",
      title: "",
      description: "",
      assignedTo: "",
      priority: "MEDIUM",
      dueDate: "",
    },
  });

  useEffect(() => {
    if (!dialogOpen) return;
    if (editing) {
      form.reset({
        projectId: editing.project_id,
        title: editing.title,
        description: editing.description ?? "",
        assignedTo: editing.assigned_to ?? "",
        priority: editing.priority,
        dueDate: editing.due_date ?? "",
      });
    } else {
      form.reset({
        projectId: "",
        title: "",
        description: "",
        assignedTo: "",
        priority: "MEDIUM",
        dueDate: "",
      });
    }
  }, [dialogOpen, editing, form]);

  const saveMutation = useMutation({
    mutationFn: (values: TaskFormValues) => {
      if (editing) {
        return updateTask(editing.id, {
          title: values.title,
          description: values.description || null,
          priority: values.priority as Task["priority"],
          assigned_to: values.assignedTo || null,
          due_date: values.dueDate || null,
        });
      }
      return createTask({
        project_id: values.projectId,
        title: values.title,
        description: values.description || null,
        assigned_to: values.assignedTo || null,
        priority: values.priority as Task["priority"],
        due_date: values.dueDate || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success(editing ? "Task updated" : "Task created");
      setDialogOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to save task"));
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      updateTask(id, { status: status as Task["status"] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("Task status updated");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to update status"));
    },
  });

  const tasks = tasksQuery.data?.items ?? [];
  const projects = projectsQuery.data?.items ?? [];
  const employees = employeesQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks"
        description={
          isEmployee
            ? "Update the status of the tasks assigned to you."
            : "Manage tasks across your projects."
        }
        actions={
          canManage ? (
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              New task
            </Button>
          ) : undefined
        }
      />

      {tasksQuery.isLoading ? (
        <LoadingState rows={4} />
      ) : tasksQuery.isError ? (
        <ErrorState message={(tasksQuery.error as Error).message} />
      ) : tasks.length === 0 ? (
        <EmptyState
          title="No tasks yet"
          description={
            isEmployee
              ? "You have no assigned tasks."
              : "Tasks will appear here once created."
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All tasks</CardTitle>
            <CardDescription>
              {tasksQuery.data?.total ?? 0} task(s).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Project</TableHead>
                  <TableHead>Assignee</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Due</TableHead>
                  <TableHead>Status</TableHead>
                  {canManage ? (
                    <TableHead className="text-right">Actions</TableHead>
                  ) : null}
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="max-w-[240px] truncate font-medium">
                      {task.title}
                    </TableCell>
                    <TableCell>{task.project_name}</TableCell>
                    <TableCell>{task.assignee_name ?? "—"}</TableCell>
                    <TableCell>
                      <StatusBadge status={task.priority} />
                    </TableCell>
                    <TableCell>{formatDate(task.due_date)}</TableCell>
                    <TableCell>
                      <Select
                        value={task.status}
                        onValueChange={(value) =>
                          statusMutation.mutate({ id: task.id, status: value })
                        }
                      >
                        <SelectTrigger className="h-8 w-[130px] text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TASK_STATUSES.map((status) => (
                            <SelectItem key={status} value={status}>
                              {status.replace(/_/g, " ")}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    {canManage ? (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            setEditing(task);
                            setDialogOpen(true);
                          }}
                          aria-label={`Edit ${task.title}`}
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
            <DialogTitle>{editing ? "Edit task" : "New task"}</DialogTitle>
            <DialogDescription>
              {editing
                ? "Update the task details."
                : "Create a new task for a project."}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))}
            className="space-y-4"
            noValidate
          >
            {!editing ? (
              <div className="space-y-1.5">
                <Label htmlFor="projectId">Project</Label>
                <Select
                  value={form.watch("projectId")}
                  onValueChange={(value) => form.setValue("projectId", value)}
                >
                  <SelectTrigger id="projectId">
                    <SelectValue placeholder="Select a project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {form.formState.errors.projectId ? (
                  <p className="text-xs text-destructive">
                    {form.formState.errors.projectId.message}
                  </p>
                ) : null}
              </div>
            ) : null}
            <div className="space-y-1.5">
              <Label htmlFor="title">Title</Label>
              <Input id="title" {...form.register("title")} />
              {form.formState.errors.title ? (
                <p className="text-xs text-destructive">
                  {form.formState.errors.title.message}
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
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="priority">Priority</Label>
                <Select
                  value={form.watch("priority")}
                  onValueChange={(value) => form.setValue("priority", value)}
                >
                  <SelectTrigger id="priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TASK_PRIORITIES.map((priority) => (
                      <SelectItem key={priority} value={priority}>
                        {priority.replace(/_/g, " ")}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="dueDate">Due date</Label>
                <Input id="dueDate" type="date" {...form.register("dueDate")} />
              </div>
            </div>
            {!isEmployee ? (
              <div className="space-y-1.5">
                <Label htmlFor="assignedTo">Assignee</Label>
                <Select
                  value={form.watch("assignedTo") ?? ""}
                  onValueChange={(value) =>
                    form.setValue("assignedTo", value === "__none" ? "" : value)
                  }
                >
                  <SelectTrigger id="assignedTo">
                    <SelectValue placeholder="Unassigned" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none">Unassigned</SelectItem>
                    {employees.map((employee) => (
                      <SelectItem key={employee.id} value={employee.id}>
                        {employee.first_name} {employee.last_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}
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
