import { requestJson } from "@/shared/api";

import type { Job } from "../model/types";

export function fetchJob(id: string): Promise<Job> {
  return requestJson(`/jobs/${id}`);
}
