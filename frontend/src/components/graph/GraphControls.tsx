"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface GraphControlsProps {
  edgeTypes: Record<string, boolean>;
  onToggleEdge: (type: string) => void;
  nodeFilter: string | null;
  onSetNodeFilter: (group: string | null) => void;
}

const NODE_GROUPS = [
  { key: "code", label: "Кодексы", color: "#4f46e5" },
  { key: "law", label: "Законы", color: "#16a34a" },
  { key: "decree", label: "Указы", color: "#9333ea" },
  { key: "resolution", label: "Постановления", color: "#6b7280" },
];

const EDGE_TYPES = [
  { key: "contradiction", label: "Противоречия", color: "#ef4444" },
  { key: "duplication", label: "Дублирования", color: "#f97316" },
  { key: "reference", label: "Ссылки", color: "#d1d5db" },
];

/** Панель управления фильтрами графа. */
export default function GraphControls({
  edgeTypes,
  onToggleEdge,
  nodeFilter,
  onSetNodeFilter,
}: GraphControlsProps) {
  return (
    <div className="absolute top-4 left-4 z-10 w-56">
      <Card className="border-border bg-background/95 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Фильтры</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Типы узлов */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Типы документов
            </p>
            <div className="flex flex-col gap-1">
              <Button
                variant={nodeFilter === null ? "secondary" : "ghost"}
                size="sm"
                className="justify-start h-7 text-xs"
                onClick={() => onSetNodeFilter(null)}
              >
                Все
              </Button>
              {NODE_GROUPS.map((g) => (
                <Button
                  key={g.key}
                  variant={nodeFilter === g.key ? "secondary" : "ghost"}
                  size="sm"
                  className="justify-start h-7 text-xs gap-2"
                  onClick={() =>
                    onSetNodeFilter(nodeFilter === g.key ? null : g.key)
                  }
                >
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: g.color }}
                  />
                  {g.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Типы рёбер */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Типы связей
            </p>
            <div className="flex flex-col gap-1">
              {EDGE_TYPES.map((e) => (
                <Button
                  key={e.key}
                  variant={edgeTypes[e.key] ? "secondary" : "ghost"}
                  size="sm"
                  className="justify-start h-7 text-xs gap-2"
                  onClick={() => onToggleEdge(e.key)}
                >
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{
                      backgroundColor: e.color,
                      opacity: edgeTypes[e.key] ? 1 : 0.3,
                    }}
                  />
                  {e.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
