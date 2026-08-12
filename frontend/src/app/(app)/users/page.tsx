"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState, EmptyState } from "@/components/data-state";
import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ShieldX } from "lucide-react";
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
import { registerUser } from "@/lib/api/auth";
import { listUsers } from "@/lib/api/users";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate, formatDateTime } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import { ROLE_CODES } from "@/lib/types";

const createUserSchema = z
  .object({
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters"),
    role: z.string().min(1, "Select a role"),
  })
  .superRefine((data, ctx) => {
    if (data.role === "ADMIN_HR") {
      ctx.addIssue({
        code: "custom",
        path: ["role"],
        message: "Only EMPLOYER or EMPLOYEE roles can be created from here",
      });
    }
  });

type CreateUserFormValues = z.infer<typeof createUserSchema>;

export default function UsersPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN_HR";
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);

  const query = useQuery({
    queryKey: ["users"],
    queryFn: () => listUsers(1, 100),
  });

  const form = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { email: "", password: "", role: "EMPLOYEE" },
  });

  useEffect(() => {
    if (dialogOpen) {
      form.reset({ email: "", password: "", role: "EMPLOYEE" });
    }
  }, [dialogOpen, form]);

  const createMutation = useMutation({
    mutationFn: (values: CreateUserFormValues) =>
      registerUser({
        email: values.email,
        password: values.password,
        role_code: values.role as (typeof ROLE_CODES)[number],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      toast.success("User created");
      setDialogOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to create user"));
    },
  });

  const users = query.data?.items ?? [];

  if (!isAdmin) {
    return (
      <Alert variant="destructive">
        <ShieldX className="h-4 w-4" />
        <AlertTitle>Access denied</AlertTitle>
        <AlertDescription>
          Only administrators can manage user accounts.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Users"
        description="Create user accounts and manage them within your company."
        actions={
          isAdmin ? (
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              Create user
            </Button>
          ) : undefined
        }
      />

      {query.isLoading ? (
        <LoadingState rows={4} />
      ) : query.isError ? (
        <ErrorState message={(query.error as Error).message} />
      ) : users.length === 0 ? (
        <EmptyState
          title="No users yet"
          description="Create a user account to get started."
          action={
            isAdmin ? (
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4" />
                Create user
              </Button>
            ) : undefined
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All users</CardTitle>
            <CardDescription>
              {query.data?.total ?? 0} user(s) in {user?.company_name}.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last login</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((userRow) => (
                  <TableRow key={userRow.id}>
                    <TableCell className="font-medium">
                      {userRow.email}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={userRow.role} />
                    </TableCell>
                    <TableCell>
                      {userRow.is_active ? "Active" : "Inactive"}
                    </TableCell>
                    <TableCell>
                      {formatDateTime(userRow.last_login_at)}
                    </TableCell>
                    <TableCell>{formatDate(userRow.created_at)}</TableCell>
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
            <DialogTitle>Create user</DialogTitle>
            <DialogDescription>
              Create an EMPLOYER or EMPLOYEE account in{" "}
              {user?.company_name ?? "your company"}.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={form.handleSubmit((v) => createMutation.mutate(v))}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="off"
                placeholder="employee@company.com"
                {...form.register("email")}
              />
              {form.formState.errors.email ? (
                <p className="text-xs text-destructive">
                  {form.formState.errors.email.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                placeholder="At least 8 characters"
                {...form.register("password")}
              />
              {form.formState.errors.password ? (
                <p className="text-xs text-destructive">
                  {form.formState.errors.password.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="role">Role</Label>
              <Select
                value={form.watch("role")}
                onValueChange={(value) => form.setValue("role", value)}
              >
                <SelectTrigger id="role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EMPLOYER">EMPLOYER</SelectItem>
                  <SelectItem value="EMPLOYEE">EMPLOYEE</SelectItem>
                </SelectContent>
              </Select>
              {form.formState.errors.role ? (
                <p className="text-xs text-destructive">
                  {form.formState.errors.role.message}
                </p>
              ) : null}
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
                {createMutation.isPending ? "Creating…" : "Create user"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
