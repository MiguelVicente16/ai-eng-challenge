import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useSessionState(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["session-state", sessionId],
    queryFn: () => api.getSessionState(sessionId!),
    enabled: !!sessionId,
    refetchInterval: sessionId ? 2000 : false,
  });
}
