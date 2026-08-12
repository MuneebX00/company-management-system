import { get, patch, post } from "@/lib/api/client";
import type { AttendanceRecord, AttendanceUpdate, Page } from "@/lib/types";

export interface AttendanceListParams {
  page?: number;
  pageSize?: number;
  fromDate?: string;
  toDate?: string;
}

export function listAttendance(params: AttendanceListParams = {}): Promise<
  Page<AttendanceRecord>
> {
  const query: Record<string, string> = {
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 50),
  };
  if (params.fromDate) query.from_date = params.fromDate;
  if (params.toDate) query.to_date = params.toDate;
  return get<Page<AttendanceRecord>>("/attendance", { params: query });
}

export function getAttendance(id: string): Promise<AttendanceRecord> {
  return get<AttendanceRecord>(`/attendance/${id}`);
}

export function checkIn(): Promise<AttendanceRecord> {
  return post<AttendanceRecord>("/attendance/check-in");
}

export function checkOut(): Promise<AttendanceRecord> {
  return post<AttendanceRecord>("/attendance/check-out");
}

export function correctAttendance(
  id: string,
  payload: AttendanceUpdate
): Promise<AttendanceRecord> {
  return patch<AttendanceRecord>(`/attendance/${id}`, payload);
}
