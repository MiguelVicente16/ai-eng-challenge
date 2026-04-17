import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api } from "@/lib/api";
import type { MetricsConfig, PhrasesConfig, ServicesConfig } from "@/lib/schemas";

export function useRouting() {
  return useQuery({ queryKey: ["routing"], queryFn: api.getRouting });
}
export function usePhrases() {
  return useQuery({ queryKey: ["phrases"], queryFn: api.getPhrases });
}
export function useMetrics() {
  return useQuery({ queryKey: ["metrics"], queryFn: api.getMetrics });
}

function onOk(key: string, qc: ReturnType<typeof useQueryClient>) {
  return {
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: [key] });
    },
    onError: (e: Error) => toast.error(e.message),
  };
}

export function usePutRouting() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (cfg: ServicesConfig) => api.putRouting(cfg), ...onOk("routing", qc) });
}
export function usePutPhrases() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (cfg: PhrasesConfig) => api.putPhrases(cfg), ...onOk("phrases", qc) });
}
export function usePutMetrics() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (cfg: MetricsConfig) => api.putMetrics(cfg), ...onOk("metrics", qc) });
}
