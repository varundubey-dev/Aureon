import type { User } from "../types/auth";

export function getUserRedirectPath(user: User) {
  if (user.is_admin) {
    return "/admin";
  }

  if (user.is_guest) {
    return "/guest";
  }

  if (user.role === "artist") {
    return "/artist/dashboard";
  }

  return "/home";
}
