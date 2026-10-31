import type { ReactNode } from "react";

export function Notice({ tone, children }: { tone: "error" | "info"; children: ReactNode }) {
  const style =
    tone === "error"
      ? "border-danger/30 bg-danger-soft text-danger"
      : "border-line bg-sunken text-muted";
  return <div className={`rounded-md border px-4 py-3 text-sm ${style}`}>{children}</div>;
}
