import { get, patch, post, remove } from "@/lib/api/client";
import type { Department, DepartmentCreate, DepartmentUpdate, Page } from "@/lib/types";

export function listDepartments(
  page = 1,
  pageSize = 50
): Promise<Page<Department>> {
  return get<Page<Department>>("/departments", {
    params: { page, page_size: pageSize },
  });
}

export function getDepartment(id: string): Promise<Department> {
  return get<Department>(`/departments/${id}`);
}

export function createDepartment(payload: DepartmentCreate): Promise<Department> {
  return post<Department>("/departments", payload);
}

export function updateDepartment(
  id: string,
  payload: DepartmentUpdate
): Promise<Department> {
  return patch<Department>(`/departments/${id}`, payload);
}

export function deleteDepartment(id: string): Promise<void> {
  return remove(`/departments/${id}`);
}
