import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { Toaster } from "sonner";

import { AppLayout } from "@/components/app-layout";
import { ThemeProvider } from "@/components/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ConfigurePage } from "@/routes/ConfigurePage";
import { SummariesPage } from "@/routes/SummariesPage";
import { SummaryDetailPage } from "@/routes/SummaryDetailPage";
import { TestChatPage } from "@/routes/TestChatPage";
import { TestVoicePage } from "@/routes/TestVoicePage";

const client = new QueryClient();

export default function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="deus-ui-theme">
      <QueryClientProvider client={client}>
        <TooltipProvider delayDuration={200}>
          <Router>
          <Routes>
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/summaries" replace />} />
              <Route path="/configure" element={<ConfigurePage />} />
              <Route path="/summaries" element={<SummariesPage />} />
              <Route path="/summaries/:id" element={<SummaryDetailPage />} />
              <Route path="/test/chat" element={<TestChatPage />} />
              <Route path="/test/voice" element={<TestVoicePage />} />
            </Route>
          </Routes>
          </Router>
          <Toaster position="top-right" richColors />
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
