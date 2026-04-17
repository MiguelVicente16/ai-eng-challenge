import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";

import { ModeToggle } from "@/components/mode-toggle";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { api } from "@/lib/api";

const TITLES: Record<string, string> = {
  "/configure": "Configure",
  "/summaries": "Summaries",
  "/test/chat": "Test Chat",
  "/test/voice": "Test Voice",
};

export function AppHeader() {
  const location = useLocation();
  const title =
    Object.entries(TITLES).find(([p]) => location.pathname.startsWith(p))?.[1] ?? "Admin";

  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.getHealth(),
    refetchInterval: 10_000,
  });
  const connected = data?.status === "ok";

  return (
    <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b border-border/70 bg-background/80 backdrop-blur-md transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
      <div className="flex flex-1 items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage className="text-[15px] font-semibold tracking-tight">
                {title}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
      <div className="flex items-center gap-2 px-4">
        <div className="flex items-center gap-1.5 rounded-full border border-border/70 bg-card px-2.5 py-1 text-xs text-foreground">
          <span
            className={`inline-block size-1.5 rounded-full ${
              connected ? "bg-[hsl(var(--success))]" : "bg-destructive"
            }`}
          />
          <span>{connected ? "connected" : "offline"}</span>
        </div>
        <ModeToggle />
      </div>
    </header>
  );
}
