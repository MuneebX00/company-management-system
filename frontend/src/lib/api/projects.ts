import { get, patch, post, remove } from "@/lib/api/client";
import type {
  Page,
  Project,
  ProjectCreate,
  ProjectMember,
  ProjectMemberAdd,
  ProjectUpdate,
} from "@/lib/types";

export function listProjects(
  page = 1,
  pageSize = 100
): Promise<Page<Project>> {
  return get<Page<Project>>("/projects", {
    params: { page, page_size: pageSize },
  });
}

export function getProject(id: string): Promise<Project> {
  return get<Project>(`/projects/${id}`);
}

export function createProject(payload: ProjectCreate): Promise<Project> {
  return post<Project>("/projects", payload);
}

export function updateProject(
  id: string,
  payload: ProjectUpdate
): Promise<Project> {
  return patch<Project>(`/projects/${id}`, payload);
}

export function deleteProject(id: string): Promise<void> {
  return remove(`/projects/${id}`);
}

export function listProjectMembers(projectId: string): Promise<ProjectMember[]> {
  return get<ProjectMember[]>(`/projects/${projectId}/members`);
}

export function addProjectMember(
  projectId: string,
  payload: ProjectMemberAdd
): Promise<ProjectMember> {
  return post<ProjectMember>(`/projects/${projectId}/members`, payload);
}

export function removeProjectMember(
  projectId: string,
  employeeId: string
): Promise<void> {
  return remove(`/projects/${projectId}/members/${employeeId}`);
}
