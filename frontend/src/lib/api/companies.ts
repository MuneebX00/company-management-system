import { get, patch, post } from "@/lib/api/client";
import type { Company, CompanyCreate, CompanyUpdate } from "@/lib/types";

export function getOwnCompany(): Promise<Company> {
  return get<Company>("/companies");
}

export function getCompany(id: string): Promise<Company> {
  return get<Company>(`/companies/${id}`);
}

export function createCompany(payload: CompanyCreate): Promise<Company> {
  return post<Company>("/companies", payload);
}

export function updateCompany(id: string, payload: CompanyUpdate): Promise<Company> {
  return patch<Company>(`/companies/${id}`, payload);
}
