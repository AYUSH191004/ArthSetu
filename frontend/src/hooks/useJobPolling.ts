import { useQuery } from "@tanstack/react-query";
import { jobsApi } from "@/api/endpoints";
import type { Job } from "@/types/api";

const TERMINAL: Job["status"][] = ["succeeded", "failed"];

export function isJobTerminal(status: Job["status"]): boolean {
  return TERMINAL.includes(status);
}

/** Polls a background job (see Docs/API_CONTRACT.md#background-jobs) until
 * it reaches a terminal state. Pass `null` to disable. */
export function useJobPolling(jobId: string | null) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => jobsApi.get(jobId as string),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const job = query.state.data as Job | undefined;
      if (!job || isJobTerminal(job.status)) return false;
      return 1500;
    },
  });
}
