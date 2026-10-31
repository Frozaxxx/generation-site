import { formatUsd } from "@/shared/lib";

import type { Job } from "../model/types";

interface JobProgressProps {
  job: Job;
  labels: Record<string, string>;
}

/** Этапы генерации по порядку: пройденные, текущий и оставшиеся. */
export function JobProgress({ job, labels }: JobProgressProps) {
  const failed = job.status === "failed";

  return (
    <div className="space-y-4">
      <ol className="space-y-2">
        {job.stages.map((stage, index) => {
          const done = job.status === "succeeded" || index < job.stage_index;
          const current = index === job.stage_index && !done;
          return (
            <li key={stage} className="flex items-start gap-3">
              <span
                className={`mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  done
                    ? "bg-accent text-white"
                    : current
                      ? failed
                        ? "bg-danger text-white"
                        : "border-2 border-accent text-accent"
                      : "border border-line text-faint"
                }`}
              >
                {done ? "✓" : index + 1}
              </span>
              <div className="min-w-0">
                <p className={`text-sm ${done || current ? "text-ink" : "text-faint"}`}>
                  {labels[stage] ?? stage}
                </p>
                {current && job.message && job.message !== labels[stage] && (
                  <p className="text-xs text-muted">{job.message}</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      <p className="text-xs text-muted">
        Потрачено {formatUsd(job.cost_usd)} из лимита {formatUsd(job.budget_usd)}, запросов к
        модели: {job.requests}
      </p>
    </div>
  );
}
