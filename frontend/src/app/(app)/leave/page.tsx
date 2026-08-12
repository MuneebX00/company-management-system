"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Plus, Pencil, Trash2, X } from "lucide-react";
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
  approveLeaveRequest,
  cancelLeaveRequest,
  createLeaveRequest,
  createLeaveType,
  deleteLeaveType,
  listLeaveRequests,
  listLeaveTypes,
  rejectLeaveRequest,
  updateLeaveType,
} from "@/lib/api/leave";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import type { LeaveRequest, LeaveType } from "@/lib/types";

const requestSchema = z.object({
  leaveTypeId: z.string().min(1, "Select a leave type"),
  startDate: z.string().min(1, "Start date is required"),
  endDate: z.string().min(1, "End date is required"),
  reason: z.string().optional(),
});

type RequestFormValues = z.infer<typeof requestSchema>;

const typeSchema = z.object({
  name: z.string().min(1, "Name is required"),
  daysPerYear: z
    .string()
    .refine(
      (value) => value !== "" && !Number.isNaN(Number(value)) && Number(value) >= 0,
      { message: "Enter a valid number of days" }
    ),
  description: z.string().optional(),
});

type TypeFormValues = z.infer<typeof typeSchema>;

type DecisionKind = "approve" | "reject" | null;

export default function LeavePage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN_HR";
  const isManager = isAdmin || user?.role === "EMPLOYER";
  const queryClient = useQueryClient();

  const [requestOpen, setRequestOpen] = useState(false);
  const [typeDialogOpen, setTypeDialogOpen] = useState(false);
  const [editingType, setEditingType] = useState<LeaveType | null>(null);
  const [deletingType, setDeletingType] = useState<LeaveType | null>(null);
  const [decision, setDecision] = useState<{
    kind: DecisionKind;
    request: LeaveRequest;
  } | null>(null);
  const [decisionNote, setDecisionNote] = useState("");

  const requestsQuery = useQuery({
    queryKey: ["leave-requests"],
    queryFn: () => listLeaveRequests(1, 100),
  });
  const typesQuery = useQuery({
    queryKey: ["leave-types"],
    queryFn: listLeaveTypes,
  });

  const requestForm = useForm<RequestFormValues>({
    resolver: zodResolver(requestSchema),
    defaultValues: {
      leaveTypeId: "",
      startDate: "",
      endDate: "",
      reason: "",
    },
  });

  const typeForm = useForm<TypeFormValues>({
    resolver: zodResolver(typeSchema),
    defaultValues: { name: "", daysPerYear: "", description: "" },
  });

  useEffect(() => {
    if (!typeDialogOpen) return;
    if (editingType) {
      typeForm.reset({
        name: editingType.name,
        daysPerYear: String(editingType.days_per_year),
        description: editingType.description ?? "",
      });
    } else {
      typeForm.reset({ name: "", daysPerYear: "", description: "" });
    }
  }, [typeDialogOpen, editingType, typeForm]);

  const createRequestMutation = useMutation({
    mutationFn: (values: RequestFormValues) =>
      createLeaveRequest({
        leave_type_id: values.leaveTypeId,
        start_date: values.startDate,
        end_date: values.endDate,
        reason: values.reason || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests"] });
      toast.success("Leave request submitted");
      setRequestOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to submit request"));
    },
  });

  const saveTypeMutation = useMutation({
    mutationFn: (values: TypeFormValues) => {
      const payload = {
        name: values.name,
        days_per_year: Number(values.daysPerYear),
        description: values.description || null,
      };
      return editingType
        ? updateLeaveType(editingType.id, payload)
        : createLeaveType(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-types"] });
      toast.success(editingType ? "Leave type updated" : "Leave type created");
      setTypeDialogOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to save leave type"));
    },
  });

  const deleteTypeMutation = useMutation({
    mutationFn: (id: string) => deleteLeaveType(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-types"] });
      toast.success("Leave type deleted");
      setDeletingType(null);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to delete leave type"));
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelLeaveRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests"] });
      toast.success("Request cancelled");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to cancel request"));
    },
  });

  const decisionMutation = useMutation({
    mutationFn: ({
      kind,
      id,
      note,
    }: {
      kind: Exclude<DecisionKind, null>;
      id: string;
      note: string;
    }) =>
      kind === "approve"
        ? approveLeaveRequest(id, note || undefined)
        : rejectLeaveRequest(id, note || undefined),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests"] });
      toast.success(variables.kind === "approve" ? "Request approved" : "Request rejected");
      setDecision(null);
      setDecisionNote("");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to update request"));
    },
  });

  const requests = requestsQuery.data?.items ?? [];
  const types = typesQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave"
        description="Submit and manage leave requests."
        actions={
          <Button onClick={() => setRequestOpen(true)}>
            <Plus className="h-4 w-4" />
            Request leave
          </Button>
        }
      />

      {requestsQuery.isLoading ? (
        <LoadingState rows={4} />
      ) : requestsQuery.isError ? (
        <ErrorState message={(requestsQuery.error as Error).message} />
      ) : requests.length === 0 ? (
        <EmptyState
          title="No leave requests"
          description="Leave requests will appear here."
          action={
            <Button onClick={() => setRequestOpen(true)}>
              <Plus className="h-4 w-4" />
              Request leave
            </Button>
          }
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Leave requests</CardTitle>
            <CardDescription>
              {requestsQuery.data?.total ?? 0} request(s).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>From</TableHead>
                  <TableHead>To</TableHead>
                  <TableHead>Days</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((request) => (
                  <TableRow key={request.id}>
                    <TableCell className="font-medium">
                      {request.employee_name}
                    </TableCell>
                    <TableCell>{request.leave_type_name}</TableCell>
                    <TableCell>{formatDate(request.start_date)}</TableCell>
                    <TableCell>{formatDate(request.end_date)}</TableCell>
                    <TableCell>{request.days}</TableCell>
                    <TableCell className="max-w-[220px] truncate">
                      {request.reason ?? "—"}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={request.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {request.status === "PENDING" && isManager ? (
                          <>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                setDecisionNote("");
                                setDecision({ kind: "approve", request });
                              }}
                              aria-label="Approve"
                            >
                              <Check className="h-4 w-4 text-emerald-600" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                setDecisionNote("");
                                setDecision({ kind: "reject", request });
                              }}
                              aria-label="Reject"
                            >
                              <X className="h-4 w-4 text-destructive" />
                            </Button>
                          </>
                        ) : null}
                        {request.status === "PENDING" ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => cancelMutation.mutate(request.id)}
                            disabled={cancelMutation.isPending}
                          >
                            Cancel
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {isAdmin ? (
        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <div>
              <CardTitle className="text-base">Leave types</CardTitle>
              <CardDescription>Manage the types of leave offered.</CardDescription>
            </div>
            <Button
              size="sm"
              onClick={() => {
                setEditingType(null);
                setTypeDialogOpen(true);
              }}
            >
              <Plus className="h-4 w-4" />
              Add type
            </Button>
          </CardHeader>
          <CardContent>
            {typesQuery.isLoading ? (
              <LoadingState rows={2} />
            ) : typesQuery.isError ? (
              <ErrorState message={(typesQuery.error as Error).message} />
            ) : types.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                No leave types yet.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Days / year</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {types.map((type) => (
                    <TableRow key={type.id}>
                      <TableCell className="font-medium">{type.name}</TableCell>
                      <TableCell>{type.days_per_year}</TableCell>
                      <TableCell className="max-w-[300px] truncate">
                        {type.description ?? "—"}
                      </TableCell>
                      <TableCell>
                        {type.is_active ? "Active" : "Inactive"}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setEditingType(type);
                              setTypeDialogOpen(true);
                            }}
                            aria-label={`Edit ${type.name}`}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeletingType(type)}
                            aria-label={`Delete ${type.name}`}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      ) : null}

      <Dialog open={requestOpen} onOpenChange={setRequestOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request leave</DialogTitle>
            <DialogDescription>
              Submit a new leave request.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={requestForm.handleSubmit((v) =>
              createRequestMutation.mutate(v)
            )}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-1.5">
              <Label htmlFor="leaveTypeId">Leave type</Label>
              <Select
                value={requestForm.watch("leaveTypeId")}
                onValueChange={(value) =>
                  requestForm.setValue("leaveTypeId", value)
                }
              >
                <SelectTrigger id="leaveTypeId">
                  <SelectValue placeholder="Select a leave type" />
                </SelectTrigger>
                <SelectContent>
                  {types.length === 0 ? (
                    <SelectItem value="__none" disabled>
                      No leave types available
                    </SelectItem>
                  ) : (
                    types.map((type) => (
                      <SelectItem key={type.id} value={type.id}>
                        {type.name} ({type.days_per_year} days/year)
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {requestForm.formState.errors.leaveTypeId ? (
                <p className="text-xs text-destructive">
                  {requestForm.formState.errors.leaveTypeId.message}
                </p>
              ) : null}
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="startDate">Start date</Label>
                <Input
                  id="startDate"
                  type="date"
                  {...requestForm.register("startDate")}
                />
                {requestForm.formState.errors.startDate ? (
                  <p className="text-xs text-destructive">
                    {requestForm.formState.errors.startDate.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="endDate">End date</Label>
                <Input
                  id="endDate"
                  type="date"
                  {...requestForm.register("endDate")}
                />
                {requestForm.formState.errors.endDate ? (
                  <p className="text-xs text-destructive">
                    {requestForm.formState.errors.endDate.message}
                  </p>
                ) : null}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="reason">Reason</Label>
              <Textarea
                id="reason"
                rows={3}
                {...requestForm.register("reason")}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setRequestOpen(false)}
                disabled={createRequestMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createRequestMutation.isPending}>
                {createRequestMutation.isPending ? "Submitting…" : "Submit"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={typeDialogOpen} onOpenChange={setTypeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingType ? "Edit leave type" : "Add leave type"}
            </DialogTitle>
            <DialogDescription>
              {editingType
                ? "Update the leave type details."
                : "Create a new type of leave."}
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={typeForm.handleSubmit((v) => saveTypeMutation.mutate(v))}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-1.5">
              <Label htmlFor="typeName">Name</Label>
              <Input id="typeName" {...typeForm.register("name")} />
              {typeForm.formState.errors.name ? (
                <p className="text-xs text-destructive">
                  {typeForm.formState.errors.name.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="daysPerYear">Days per year</Label>
              <Input
                id="daysPerYear"
                type="number"
                min={0}
                {...typeForm.register("daysPerYear")}
              />
              {typeForm.formState.errors.daysPerYear ? (
                <p className="text-xs text-destructive">
                  {typeForm.formState.errors.daysPerYear.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="typeDescription">Description</Label>
              <Textarea
                id="typeDescription"
                rows={3}
                {...typeForm.register("description")}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setTypeDialogOpen(false)}
                disabled={saveTypeMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={saveTypeMutation.isPending}>
                {saveTypeMutation.isPending ? "Saving…" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={decision !== null}
        onOpenChange={(open) => {
          if (!open) setDecision(null);
        }}
        title={decision?.kind === "approve" ? "Approve leave request" : "Reject leave request"}
        description={
          decision
            ? `${decision.kind === "approve" ? "Approve" : "Reject"} ${decision.request.employee_name}'s ${decision.request.leave_type_name} request from ${formatDate(decision.request.start_date)} to ${formatDate(decision.request.end_date)}?`
            : undefined
        }
        confirmLabel={decision?.kind === "approve" ? "Approve" : "Reject"}
        destructive={decision?.kind === "reject"}
        loading={decisionMutation.isPending}
        onConfirm={() => {
          if (decision) {
            decisionMutation.mutate({
              kind: decision.kind!,
              id: decision.request.id,
              note: decisionNote,
            });
          }
        }}
      >
        <div className="space-y-1.5">
          <Label htmlFor="decisionNote">Note (optional)</Label>
          <Textarea
            id="decisionNote"
            rows={3}
            value={decisionNote}
            onChange={(e) => setDecisionNote(e.target.value)}
          />
        </div>
      </ConfirmDialog>

      <ConfirmDialog
        open={deletingType !== null}
        onOpenChange={(open) => {
          if (!open) setDeletingType(null);
        }}
        title="Delete leave type"
        description={`Are you sure you want to delete "${deletingType?.name}"?`}
        confirmLabel="Delete"
        destructive
        loading={deleteTypeMutation.isPending}
        onConfirm={() => {
          if (deletingType) deleteTypeMutation.mutate(deletingType.id);
        }}
      />
    </div>
  );
}
