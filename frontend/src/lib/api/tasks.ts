import { get, patch, post } from "@/lib/api/client";
import type { Page, Task, TaskAssign, TaskCreate, TaskUpdate } from "@/lib/types";

export function listTasks(
  page = 1,
  pageSize = 100
): Promise<Page<Task>> {
  return get<Page<Task>>("/tasks", {
    params: { page, page_size: pageSize },
  });
}

export function getTask(id: string): Promise<Task> {
  return get<Task>(`/tasks/${id}`);
}

export function createTask(payload: TaskCreate): Promise<Task> {
  return post<Task>("/tasks", payload);
}

export function updateTask(id: string, payload: TaskUpdate): Promise<Task> {
  return patch<Task>(`/tasks/${id}`, payload);
}

export function assignTask(id: string, payload: TaskAssign): Promise<Task> {
  return post<Task>(`/tasks/${id}/assign`, payload);
}
