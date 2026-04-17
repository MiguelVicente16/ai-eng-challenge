import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricsTab } from "@/features/configure/MetricsTab";
import { PhrasesTab } from "@/features/configure/PhrasesTab";
import { ServicesTab } from "@/features/configure/ServicesTab";

const SECTIONS: Record<string, { title: string; caption: string }> = {
  services: {
    title: "Services",
    caption: "Configure how the assistant routes incoming calls to your teams.",
  },
  phrases: {
    title: "Phrases",
    caption:
      "Edit what the assistant says, word for word. Variables in {braces} are filled in at runtime.",
  },
  metrics: {
    title: "Metrics",
    caption:
      "Define what the post-call summarizer extracts. Add, rename, or change types — the schema adapts automatically.",
  },
};

export function ConfigurePage() {
  return (
    <Tabs defaultValue="services" className="w-full">
      <TabsList>
        <TabsTrigger value="services">Services</TabsTrigger>
        <TabsTrigger value="phrases">Phrases</TabsTrigger>
        <TabsTrigger value="metrics">Metrics</TabsTrigger>
      </TabsList>

      {Object.entries(SECTIONS).map(([key, section]) => (
        <TabsContent key={key} value={key} className="mt-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">
              {section.title}
            </h2>
            <p className="max-w-2xl text-sm text-muted-foreground">
              {section.caption}
            </p>
          </div>
          {key === "services" && <ServicesTab />}
          {key === "phrases" && <PhrasesTab />}
          {key === "metrics" && <MetricsTab />}
        </TabsContent>
      ))}
    </Tabs>
  );
}
