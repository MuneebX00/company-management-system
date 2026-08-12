import { get, patch, post } from "@/lib/api/client";
import type { Employee, EmployeeCreate, EmployeeUpdate, Page } from "@/lib/types";

export function listEmployees(
  page = 1,
  pageSize = 100
): Promise<Page<Employee>> {
  return get<Page<Employee>>("/employees", {
    params: { page, page_size: pageSize },
  });
}

export function getMyEmployeeProfile(): Promise<Employee> {
  return get<Employee>("/employees/me");
}

export function getEmployee(id: string): Promise<Employee> {
  return get<Employee>(`/employees/${id}`);
}

export function createEmployee(payload: EmployeeCreate): Promise<Employee> {
  return post<Employee>("/employees", payload);
}

export function updateEmployee(
  id: string,
  payload: EmployeeUpdate
): Promise<Employee> {
  return patch<Employee>(`/employees/${id}`, payload);
}
