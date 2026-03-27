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
  { key: "code", label: "Кодексы", color: "#3B82F6" },
  { key: "law", label: "Законы", color: "#059669" },
  { key: "decree", label: "Указы", color: "#9333ea" },
  { key: "resolution", label: "Постановления", color: "#64748B" },
];

const EDGE_TYPES = [
  { key: "contradiction", label: "Противоречия", color: "#DC2626" },
  { key: "duplication", label: "Дублирования", color: "#D97706" },
  { key: "reference", label: "Ссылки", color: "#94A3B8" },
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
      <Card className="border-white/10 bg-[#0E1223]/90 backdrop-blur-xl shadow-2xl shadow-black/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-white/90">Фильтры</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Типы узлов */}
          <div>
            <p className="text-xs font-medium text-white/50 mb-1.5">
              Типы документов
            </p>
            <div className="flex flex-col gap-1">
              <Button
                variant={nodeFilter === null ? "secondary" : "ghost"}
                size="sm"
                className="justify-start h-7 text-xs text-white/80 hover:text-white hover:bg-white/10"
                onClick={() => onSetNodeFilter(null)}
              >
                Все
              </Button>
              {NODE_GROUPS.map((g) => (
                <Button
                  key={g.key}
                  variant={nodeFilter === g.key ? "secondary" : "ghost"}
                  size="sm"
                  className="justify-start h-7 text-xs gap-2 text-white/80 hover:text-white hover:bg-white/10"
                  onClick={() =>
                    onSetNodeFilter(nodeFilter === g.key ? null : g.key)
                  }
                >
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full ring-1 ring-white/20"
                    style={{ backgroundColor: g.color }}
                  />
                  {g.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Типы рёбер */}
          <div>
            <p className="text-xs font-medium text-white/50 mb-1.5">
              Типы связей
            </p>
            <div className="flex flex-col gap-1">
              {EDGE_TYPES.map((e) => (
                <Button
                  key={e.key}
                  variant={edgeTypes[e.key] ? "secondary" : "ghost"}
                  size="sm"
                  className="justify-start h-7 text-xs gap-2 text-white/80 hover:text-white hover:bg-white/10"
                  onClick={() => onToggleEdge(e.key)}
                >
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full ring-1 ring-white/20"
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
