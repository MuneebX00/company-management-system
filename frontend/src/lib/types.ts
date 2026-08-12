export type Role = "ADMIN_HR" | "EMPLOYER" | "EMPLOYEE";

export type EmploymentStatus =
  | "ACTIVE"
  | "ON_LEAVE"
  | "SUSPENDED"
  | "TERMINATED";

export type AttendanceStatus =
  | "PRESENT"
  | "LATE"
  | "ABSENT"
  | "HALF_DAY"
  | "ON_LEAVE";

export type LeaveStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

export type ProjectStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "ON_HOLD"
  | "COMPLETED"
  | "CANCELLED";

export type TaskStatus = "TODO" | "IN_PROGRESS" | "IN_REVIEW" | "DONE" | "CANCELLED";

export type TaskPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export const ROLE_CODES: Role[] = ["ADMIN_HR", "EMPLOYER", "EMPLOYEE"];

export const EMPLOYMENT_STATUSES: EmploymentStatus[] = [
  "ACTIVE",
  "ON_LEAVE",
  "SUSPENDED",
  "TERMINATED",
];

export const ATTENDANCE_STATUSES: AttendanceStatus[] = [
  "PRESENT",
  "LATE",
  "ABSENT",
  "HALF_DAY",
  "ON_LEAVE",
];

export const LEAVE_STATUSES: LeaveStatus[] = [
  "PENDING",
  "APPROVED",
  "REJECTED",
  "CANCELLED",
];

export const PROJECT_STATUSES: ProjectStatus[] = [
  "NOT_STARTED",
  "IN_PROGRESS",
  "ON_HOLD",
  "COMPLETED",
  "CANCELLED",
];

export const TASK_STATUSES: TaskStatus[] = [
  "TODO",
  "IN_PROGRESS",
  "IN_REVIEW",
  "DONE",
  "CANCELLED",
];

export const TASK_PRIORITIES: TaskPriority[] = ["LOW", "MEDIUM", "HIGH", "URGENT"];

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserMe {
  id: string;
  email: string;
  role: Role;
  company_id: string;
  company_name: string;
  is_active: boolean;
  last_login_at: string | null;
}

export interface User {
  id: string;
  email: string;
  role: Role;
  company_id: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  role_code: Role;
}

export interface Company {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyCreate {
  name: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
}

export interface CompanyUpdate {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  is_active?: boolean | null;
}

export interface Department {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DepartmentCreate {
  name: string;
  description?: string | null;
}

export interface DepartmentUpdate {
  name?: string | null;
  description?: string | null;
  is_active?: boolean | null;
}

export interface Employer {
  id: string;
  company_id: string;
  department_id: string | null;
  department_name: string | null;
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  job_title: string | null;
  hire_date: string | null;
  created_at: string;
}

export interface EmployerCreate {
  user_id: string;
  department_id?: string | null;
  first_name: string;
  last_name: string;
  job_title?: string | null;
  hire_date?: string | null;
}

export interface EmployerUpdate {
  department_id?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  job_title?: string | null;
  hire_date?: string | null;
}

export interface Employee {
  id: string;
  company_id: string;
  department_id: string | null;
  department_name: string | null;
  employer_id: string | null;
  manager_name: string | null;
  user_id: string;
  email: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  job_title: string | null;
  hire_date: string | null;
  employment_status: EmploymentStatus;
  phone: string | null;
  created_at: string;
}

export interface EmployeeCreate {
  user_id: string;
  department_id?: string | null;
  employer_id?: string | null;
  employee_number: string;
  first_name: string;
  last_name: string;
  job_title?: string | null;
  hire_date?: string | null;
  employment_status: EmploymentStatus;
  phone?: string | null;
}

export interface EmployeeUpdate {
  department_id?: string | null;
  employer_id?: string | null;
  employee_number?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  job_title?: string | null;
  employment_status?: EmploymentStatus | null;
  phone?: string | null;
}

export interface AttendanceRecord {
  id: string;
  company_id: string;
  employee_id: string;
  employee_name: string;
  work_date: string;
  check_in_at: string | null;
  check_out_at: string | null;
  hours_worked: string | null;
  status: AttendanceStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceUpdate {
  work_date?: string | null;
  check_in_at?: string | null;
  check_out_at?: string | null;
  status?: AttendanceStatus | null;
  notes?: string | null;
}

export interface LeaveType {
  id: string;
  company_id: string;
  name: string;
  days_per_year: number;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LeaveTypeCreate {
  name: string;
  days_per_year?: number;
  description?: string | null;
}

export interface LeaveTypeUpdate {
  name?: string | null;
  days_per_year?: number | null;
  description?: string | null;
  is_active?: boolean | null;
}

export interface LeaveRequest {
  id: string;
  company_id: string;
  employee_id: string;
  employee_name: string;
  leave_type_id: string;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  days: number;
  status: LeaveStatus;
  reason: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  decision_note: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeaveRequestCreate {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason?: string | null;
}

export interface Project {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  owner_id: string | null;
  owner_name: string | null;
  created_by: string;
  start_date: string | null;
  end_date: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
  owner_id?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface ProjectUpdate {
  name?: string | null;
  description?: string | null;
  status?: ProjectStatus | null;
  owner_id?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface ProjectMember {
  project_id: string;
  employee_id: string;
  employee_name: string;
  role: string | null;
}

export interface ProjectMemberAdd {
  employee_id: string;
  role?: string | null;
}

export interface Task {
  id: string;
  company_id: string;
  project_id: string;
  project_name: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_to: string | null;
  assignee_name: string | null;
  assigned_by: string | null;
  created_by: string;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  project_id: string;
  title: string;
  description?: string | null;
  assigned_to?: string | null;
  priority?: TaskPriority;
  due_date?: string | null;
}

export interface TaskUpdate {
  title?: string | null;
  description?: string | null;
  status?: TaskStatus | null;
  priority?: TaskPriority | null;
  assigned_to?: string | null;
  due_date?: string | null;
}

export interface TaskAssign {
  assigned_to: string;
}
