import axios from "axios";

import { get, post } from "@/lib/api/client";
import type { TokenResponse, User, UserCreate, UserMe } from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_PYTHON_API_URL ?? "http://127.0.0.1:8000/api/v1";

export async function loginRequest(
  email: string,
  password: string
): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);
  const { data } = await axios.post<TokenResponse>(
    `${API_URL}/auth/login`,
    body,
    { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
  );
  return data;
}

export function fetchMe(): Promise<UserMe> {
  return get<UserMe>("/auth/me");
}

export async function logoutRequest(refreshToken: string): Promise<void> {
  try {
    await post("/auth/logout", { refresh_token: refreshToken });
  } catch {
    // best-effort: local logout still proceeds
  }
}

export function registerUser(payload: UserCreate): Promise<User> {
  return post<User>("/auth/register", payload);
}
