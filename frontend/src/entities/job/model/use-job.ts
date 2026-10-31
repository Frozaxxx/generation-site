import { useEffect, useState } from "react";

import { errorMessage } from "@/shared/api";

import { fetchJob } from "../api/job-api";
import { isFinished, type Job } from "./types";

const POLL_MS = 1500;

/** Опрашивает задачу, пока она не завершится. Опрос бесплатный: читает только базу. */
export function useJob(initial: Job | null): { job: Job | null; error: string | null } {
  const [job, setJob] = useState<Job | null>(initial);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setJob(initial);
  }, [initial]);

  useEffect(() => {
    if (!job || isFinished(job)) return undefined;

    const timer = window.setTimeout(async () => {
      try {
        setJob(await fetchJob(job.id));
        setError(null);
      } catch (cause) {
        setError(errorMessage(cause));
      }
    }, POLL_MS);
    return () => window.clearTimeout(timer);
  }, [job]);

  return { job, error };
}
