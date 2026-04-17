import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ThemeProvider, useTheme } from "@/components/theme-provider";

function _Probe() {
  const { theme } = useTheme();
  return <span data-testid="theme">{theme}</span>;
}

describe("ThemeProvider", () => {
  it("should_default_to_light_theme", () => {
    // Arrange + Act
    render(
      <ThemeProvider defaultTheme="light" storageKey="test">
        <_Probe />
      </ThemeProvider>,
    );

    // Assert
    expect(screen.getByTestId("theme")).toHaveTextContent("light");
  });
});
