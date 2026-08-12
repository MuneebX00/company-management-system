import { get, patch, post, remove } from "@/lib/api/client";
import type {
  LeaveRequest,
  LeaveRequestCreate,
  LeaveType,
  LeaveTypeCreate,
  LeaveTypeUpdate,
  Page,
} from "@/lib/types";

export function listLeaveTypes(): Promise<Page<LeaveType>> {
  return get<Page<LeaveType>>("/leave/types", {
    params: { page: 1, page_size: 100 },
  });
}

export function createLeaveType(payload: LeaveTypeCreate): Promise<LeaveType> {
  return post<LeaveType>("/leave/types", payload);
}

export function updateLeaveType(
  id: string,
  payload: LeaveTypeUpdate
): Promise<LeaveType> {
  return patch<LeaveType>(`/leave/types/${id}`, payload);
}

export function deleteLeaveType(id: string): Promise<void> {
  return remove(`/leave/types/${id}`);
}

export function listLeaveRequests(
  page = 1,
  pageSize = 100
): Promise<Page<LeaveRequest>> {
  return get<Page<LeaveRequest>>("/leave/requests", {
    params: { page, page_size: pageSize },
  });
}

export function createLeaveRequest(
  payload: LeaveRequestCreate
): Promise<LeaveRequest> {
  return post<LeaveRequest>("/leave/requests", payload);
}

export function updateLeaveRequest(
  id: string,
  payload: LeaveRequestCreate
): Promise<LeaveRequest> {
  return patch<LeaveRequest>(`/leave/requests/${id}`, payload);
}

export function approveLeaveRequest(id: string, note?: string): Promise<LeaveRequest> {
  return post<LeaveRequest>(`/leave/requests/${id}/approve`, { note: note ?? null });
}

export function rejectLeaveRequest(id: string, note?: string): Promise<LeaveRequest> {
  return post<LeaveRequest>(`/leave/requests/${id}/reject`, { note: note ?? null });
}

export function cancelLeaveRequest(id: string): Promise<LeaveRequest> {
  return post<LeaveRequest>(`/leave/requests/${id}/cancel`);
}
