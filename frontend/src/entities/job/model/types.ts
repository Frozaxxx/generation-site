export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface Job {
  id: string;
  kind: "company" | "site";
  status: JobStatus;
  stages: string[];
  stage: string | null;
  stage_index: number;
  progress: number;
  message: string;
  subject_id: string | null;
  result_id: string | null;
  cost_usd: number;
  budget_usd: number;
  requests: number;
  error: { code: string; message: string; details: unknown } | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export function isFinished(job: Job): boolean {
  return job.status === "succeeded" || job.status === "failed";
}
