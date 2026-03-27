"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { GraphNode, GraphLink } from "@/lib/types";

interface GraphNodeInfoProps {
  node: GraphNode | null;
  link: GraphLink | null;
  onClose: () => void;
}

const GROUP_LABELS: Record<string, string> = {
  code: "Кодекс",
  law: "Закон",
  decree: "Указ",
  resolution: "Постановление",
  order: "Приказ",
};

const LINK_TYPE_LABELS: Record<string, string> = {
  contradiction: "Противоречие",
  duplication: "Дублирование",
  reference: "Ссылка",
};

/** Боковая панель с информацией о выбранном узле или ребре графа. */
export default function GraphNodeInfo({ node, link, onClose }: GraphNodeInfoProps) {
  if (!node && !link) return null;

  return (
    <div className="absolute top-4 right-4 z-10 w-80">
      <Card className="border-border bg-background/95 backdrop-blur-sm">
        <CardHeader className="pb-2 flex flex-row items-start justify-between">
          <CardTitle className="text-sm">
            {node ? "Документ" : "Связь"}
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0">
            &times;
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {node && (
            <>
              <p className="text-sm font-medium text-foreground leading-snug">
                {node.name}
              </p>
              <div className="flex items-center gap-2">
                {node.group && (
                  <Badge variant="outline">
                    {GROUP_LABELS[node.group] ?? node.group}
                  </Badge>
                )}
                <span className="text-xs text-muted-foreground">
                  Размер: {node.val}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">ID: {node.id}</p>
            </>
          )}
          {link && (
            <>
              <p className="text-sm text-foreground">
                <span className="font-medium">Источник:</span> {String(link.source)}
              </p>
              <p className="text-sm text-foreground">
                <span className="font-medium">Цель:</span> {String(link.target)}
              </p>
              {link.type && (
                <Badge variant="outline">
                  {LINK_TYPE_LABELS[link.type] ?? link.type}
                </Badge>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
