import { MessageSquare, Mic, Settings2, Sparkles, Table2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink } from "react-router-dom";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

type NavItem = { to: string; label: string; icon: LucideIcon };

const ITEMS: NavItem[] = [
  { to: "/configure", label: "Configure", icon: Settings2 },
  { to: "/summaries", label: "Summaries", icon: Table2 },
  { to: "/test/chat", label: "Test Chat", icon: MessageSquare },
  { to: "/test/voice", label: "Test Voice", icon: Mic },
];

export function AppSidebar() {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <NavLink to="/summaries">
                <div className="flex aspect-square size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
                  <Sparkles className="size-4" />
                </div>
                <div className="grid flex-1 text-left leading-tight">
                  <span className="text-sm font-semibold tracking-tight">DEUS Admin</span>
                  <span className="text-xs text-muted-foreground">AI support console</span>
                </div>
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {ITEMS.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton asChild tooltip={item.label}>
                    <NavLink
                      to={item.to}
                      className={({ isActive }) =>
                        cn(
                          "relative",
                          isActive &&
                            "bg-sidebar-accent/10 font-medium text-foreground",
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon
                            className={cn(
                              "shrink-0",
                              isActive ? "text-[hsl(var(--brand))]" : "text-muted-foreground",
                            )}
                          />
                          <span>{item.label}</span>
                        </>
                      )}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <div className="px-2 pb-1 text-[11px] text-muted-foreground group-data-[collapsible=icon]:hidden">
          v1.0
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
