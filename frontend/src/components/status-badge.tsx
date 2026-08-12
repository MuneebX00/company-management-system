import type { VariantProps } from "class-variance-authority";

import { Badge, type badgeVariants } from "@/components/ui/badge";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

const STATUS_VARIANTS: Record<string, BadgeVariant> = {
  ACTIVE: "success",
  ON_LEAVE: "warning",
  SUSPENDED: "destructive",
  TERMINATED: "muted",
  PRESENT: "success",
  LATE: "warning",
  ABSENT: "destructive",
  HALF_DAY: "info",
  PENDING: "warning",
  APPROVED: "success",
  REJECTED: "destructive",
  CANCELLED: "muted",
  NOT_STARTED: "muted",
  IN_PROGRESS: "info",
  ON_HOLD: "warning",
  COMPLETED: "success",
  TODO: "muted",
  IN_REVIEW: "warning",
  DONE: "success",
  LOW: "muted",
  MEDIUM: "info",
  HIGH: "warning",
  URGENT: "destructive",
};

export function StatusBadge({ status }: { status: string }) {
  const variant = STATUS_VARIANTS[status] ?? "secondary";
  return <Badge variant={variant}>{status.replace(/_/g, " ")}</Badge>;
}
