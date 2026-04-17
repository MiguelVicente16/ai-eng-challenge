import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";

describe("AppSidebar", () => {
  it("should_render_all_four_nav_items", () => {
    // Arrange + Act
    render(
      <MemoryRouter>
        <TooltipProvider>
          <SidebarProvider>
            <AppSidebar />
          </SidebarProvider>
        </TooltipProvider>
      </MemoryRouter>,
    );

    // Assert
    expect(screen.getByText("Configure")).toBeInTheDocument();
    expect(screen.getByText("Summaries")).toBeInTheDocument();
    expect(screen.getByText("Test Chat")).toBeInTheDocument();
    expect(screen.getByText("Test Voice")).toBeInTheDocument();
  });
});
