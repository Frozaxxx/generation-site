import { Badge } from "@/shared/ui";

import { STATUS_LABELS } from "../lib/labels";
import type { CompanyStatus } from "../model/types";

export function StatusBadge({ status }: { status: CompanyStatus }) {
  return <Badge tone={status === "approved" ? "accent" : "neutral"}>{STATUS_LABELS[status]}</Badge>;
}
