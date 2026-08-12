"use client";

import {
  Building2,
  CalendarClock,
  CalendarDays,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  MapPin,
  Palette,
  Users,
  UserRound,
  UserRoundCheck,
  UserCog,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const NAV_GROUPS: {
  label: string;
  items: { href: string; label: string; icon: React.ComponentType<{ className?: string }>; roles: string[] }[];
}[] = [
  {
    label: "Overview",
    items: [
      {
        href: "/dashboard",
        label: "Dashboard",
        icon: LayoutDashboard,
        roles: ["ADMIN_HR", "EMPLOYER", "EMPLOYEE"],
      },
    ],
  },
  {
    label: "Organization",
    items: [
      {
        href: "/company",
        label: "Company",
        icon: Building2,
        roles: ["ADMIN_HR"],
      },
      {
        href: "/departments",
        label: "Departments",
        icon: MapPin,
        roles: ["ADMIN_HR"],
      },
      {
        href: "/employers",
        label: "Employers",
        icon: UserRoundCheck,
        roles: ["ADMIN_HR"],
      },
      {
        href: "/employees",
        label: "Employees",
        icon: Users,
        roles: ["ADMIN_HR", "EMPLOYER"],
      },
      {
        href: "/users",
        label: "Users",
        icon: UserCog,
        roles: ["ADMIN_HR"],
      },
    ],
  },
  {
    label: "Operations",
    items: [
      {
        href: "/attendance",
        label: "Attendance",
        icon: CalendarClock,
        roles: ["ADMIN_HR", "EMPLOYER", "EMPLOYEE"],
      },
      {
        href: "/leave",
        label: "Leave",
        icon: CalendarDays,
        roles: ["ADMIN_HR", "EMPLOYER", "EMPLOYEE"],
      },
      {
        href: "/projects",
        label: "Projects",
        icon: ClipboardList,
        roles: ["ADMIN_HR", "EMPLOYER", "EMPLOYEE"],
      },
      {
        href: "/tasks",
        label: "Tasks",
        icon: ClipboardList,
        roles: ["ADMIN_HR", "EMPLOYER", "EMPLOYEE"],
      },
    ],
  },
  {
    label: "Account",
    items: [
      {
        href: "/profile",
        label: "Profile",
        icon: UserRound,
        roles: ["ADMIN_HR", "EMPLOYER", "EMPLOYEE"],
      },
    ],
  },
];

function SidebarNav() {
  const { user } = useAuth();
  const pathname = usePathname();

  if (!user) return null;

  const groups = NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => item.roles.includes(user.role)),
  })).filter((group) => group.items.length > 0);

  return (
    <nav className="flex flex-col gap-6 px-3 py-4">
      {groups.map((group) => (
        <div key={group.label} className="flex flex-col gap-1">
          <p className="px-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {group.label}
          </p>
          {group.items.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    try {
      await logout();
      toast.success("Signed out");
    } catch {
      // tokens already cleared in logout()
    }
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r bg-background md:flex">
        <div className="flex h-16 items-center border-b px-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <Palette className="h-5 w-5 text-primary" />
            <span className="text-lg font-semibold tracking-tight">
              CMS Portal
            </span>
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto">
          <SidebarNav />
        </div>
        <div className="border-t p-4">
          <div className="mb-3 px-2">
            <p className="truncate text-sm font-medium">{user?.email}</p>
            <p className="truncate text-xs text-muted-foreground">
              {user?.company_name}
            </p>
          </div>
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>
      <div className="md:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-2 border-b bg-background/95 px-6 backdrop-blur md:hidden">
          <Link href="/dashboard" className="flex items-center gap-2">
            <Palette className="h-5 w-5 text-primary" />
            <span className="font-semibold">CMS Portal</span>
          </Link>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl px-6 py-8">{children}</main>
      </div>
    </div>
  );
}
