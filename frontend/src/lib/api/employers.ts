import { get, patch, post } from "@/lib/api/client";
import type { Employer, EmployerCreate, EmployerUpdate, Page } from "@/lib/types";

export function listEmployers(
  page = 1,
  pageSize = 50
): Promise<Page<Employer>> {
  return get<Page<Employer>>("/employers", {
    params: { page, page_size: pageSize },
  });
}

export function getEmployer(id: string): Promise<Employer> {
  return get<Employer>(`/employers/${id}`);
}

export function createEmployer(payload: EmployerCreate): Promise<Employer> {
  return post<Employer>("/employers", payload);
}

export function updateEmployer(
  id: string,
  payload: EmployerUpdate
): Promise<Employer> {
  return patch<Employer>(`/employers/${id}`, payload);
}
