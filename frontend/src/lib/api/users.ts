import { get } from "@/lib/api/client";
import type { Page, User } from "@/lib/types";

export function listUsers(page = 1, pageSize = 100): Promise<Page<User>> {
  return get<Page<User>>("/users", {
    params: { page, page_size: pageSize },
  });
}

export function getUser(id: string): Promise<User> {
  return get<User>(`/users/${id}`);
}
