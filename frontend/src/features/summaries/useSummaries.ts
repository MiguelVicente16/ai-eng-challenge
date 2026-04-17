import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export type SummaryFilters = {
  page: number;
  size: number;
  sentiment?: string;
  resolved?: boolean | "";
  q?: string;
  from?: string;
  to?: string;
};

export function useSummariesQuery(filters: SummaryFilters) {
  return useQuery({
    queryKey: ["summaries", filters],
    queryFn: () =>
      api.listSummaries({
        page: filters.page,
        size: filters.size,
        sentiment: filters.sentiment || undefined,
        resolved: filters.resolved === "" ? undefined : filters.resolved,
        q: filters.q || undefined,
        from: filters.from || undefined,
        to: filters.to || undefined,
      }),
    placeholderData: (prev) => prev,
  });
}
