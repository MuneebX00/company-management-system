"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LogIn, LogOut, Pencil } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

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
import {
  checkIn,
  checkOut,
  correctAttendance,
  listAttendance,
} from "@/lib/api/attendance";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate, formatTime, todayIso } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import {
  ATTENDANCE_STATUSES,
  type AttendanceRecord,
} from "@/lib/types";

export default function AttendancePage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN_HR";
  const queryClient = useQueryClient();
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [correcting, setCorrecting] = useState<AttendanceRecord | null>(null);
  const [status, setStatus] = useState("PRESENT");
  const [notes, setNotes] = useState("");

  const query = useQuery({
    queryKey: ["attendance", { from: fromDate, to: toDate }],
    queryFn: () =>
      listAttendance({
        fromDate: fromDate || undefined,
        toDate: toDate || undefined,
      }),
  });

  const checkInMutation = useMutation({
    mutationFn: checkIn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
      toast.success("Checked in");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Check-in failed"));
    },
  });

  const checkOutMutation = useMutation({
    mutationFn: checkOut,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
      toast.success("Checked out");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Check-out failed"));
    },
  });

  const correctMutation = useMutation({
    mutationFn: (values: { id: string; status: string; notes: string }) =>
      correctAttendance(values.id, {
        status: values.status as AttendanceRecord["status"],
        notes: values.notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
      toast.success("Record corrected");
      setCorrecting(null);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to correct record"));
    },
  });

  const records = query.data?.items ?? [];
  const today = records.find((r) => r.work_date === todayIso());

  function openCorrect(record: AttendanceRecord) {
    setCorrecting(record);
    setStatus(record.status);
    setNotes(record.notes ?? "");
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        description="Check in and out, and review attendance records."
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => checkInMutation.mutate()}
              disabled={checkInMutation.isPending || !!today?.check_in_at}
            >
              <LogIn className="h-4 w-4" />
              {checkInMutation.isPending ? "Checking in…" : "Check in"}
            </Button>
            <Button
              onClick={() => checkOutMutation.mutate()}
              disabled={checkOutMutation.isPending || !today?.check_in_at}
            >
              <LogOut className="h-4 w-4" />
              {checkOutMutation.isPending ? "Checking out…" : "Check out"}
            </Button>
          </div>
        }
      />

      {today ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Today</CardTitle>
            <CardDescription>
              {today.work_date} ·{" "}
              {today.status.replace(/_/g, " ").toLowerCase()}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-6 text-sm">
            <div>
              <p className="text-muted-foreground">Check in</p>
              <p className="font-medium">{formatTime(today.check_in_at)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Check out</p>
              <p className="font-medium">{formatTime(today.check_out_at)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Hours</p>
              <p className="font-medium">
                {today.hours_worked ? `${today.hours_worked} h` : "—"}
              </p>
            </div>
            <div>
              <StatusBadge status={today.status} />
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <Input
          type="date"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          className="w-auto"
          aria-label="From date"
        />
        <Input
          type="date"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          className="w-auto"
          aria-label="To date"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setFromDate("");
            setToDate("");
          }}
        >
          Clear
        </Button>
      </div>

      {query.isLoading ? (
        <LoadingState rows={4} />
      ) : query.isError ? (
        <ErrorState message={(query.error as Error).message} />
      ) : records.length === 0 ? (
        <EmptyState
          title="No attendance records"
          description="Records will appear here once employees check in."
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Records</CardTitle>
            <CardDescription>
              {query.data?.total ?? 0} record(s).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Employee</TableHead>
                  <TableHead>Check in</TableHead>
                  <TableHead>Check out</TableHead>
                  <TableHead>Hours</TableHead>
                  <TableHead>Status</TableHead>
                  {isAdmin ? (
                    <TableHead className="text-right">Actions</TableHead>
                  ) : null}
                </TableRow>
              </TableHeader>
              <TableBody>
                {records.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>{formatDate(record.work_date)}</TableCell>
                    <TableCell className="font-medium">
                      {record.employee_name}
                    </TableCell>
                    <TableCell>{formatTime(record.check_in_at)}</TableCell>
                    <TableCell>{formatTime(record.check_out_at)}</TableCell>
                    <TableCell>
                      {record.hours_worked ? `${record.hours_worked} h` : "—"}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={record.status} />
                    </TableCell>
                    {isAdmin ? (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => openCorrect(record)}
                          aria-label="Correct record"
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

      <Dialog
        open={correcting !== null}
        onOpenChange={(open) => {
          if (!open) setCorrecting(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Correct attendance record</DialogTitle>
            <DialogDescription>
              Update the status and notes for {correcting?.employee_name} on{" "}
              {correcting ? formatDate(correcting.work_date) : ""}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="status">Status</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ATTENDANCE_STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s.replace(/_/g, " ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCorrecting(null)}
              disabled={correctMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={() =>
                correcting &&
                correctMutation.mutate({
                  id: correcting.id,
                  status,
                  notes,
                })
              }
              disabled={correctMutation.isPending}
            >
              {correctMutation.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
