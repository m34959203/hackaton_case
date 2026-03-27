"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { GraphNode, GraphLink } from "@/lib/types";
import { typeLabel } from "@/lib/utils";
import Link from "next/link";

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
              <div className="flex flex-wrap items-center gap-2">
                {node.group && (
                  <Badge variant="outline">
                    {GROUP_LABELS[node.group] ?? node.group}
                  </Badge>
                )}
                {node.status && (
                  <Badge variant={node.status === "active" ? "secondary" : "outline"}>
                    {typeLabel(node.status)}
                  </Badge>
                )}
              </div>
              {node.domain && (
                <p className="text-xs text-muted-foreground">
                  {node.domain}
                </p>
              )}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-muted-foreground">Норм:</span>{" "}
                  <span className="font-medium">{node.val}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Обнаружений:</span>{" "}
                  <span className={node.findingsCount > 0 ? "font-medium text-red-400" : "font-medium"}>
                    {node.findingsCount}
                  </span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground font-mono">
                ID: {node.id}
              </p>
              <Link
                href={`/documents/${encodeURIComponent(node.id)}`}
                className="inline-block text-xs text-blue-400 hover:underline mt-1"
              >
                Открыть документ
              </Link>
            </>
          )}
          {link && (
            <>
              <div className="space-y-1">
                <p className="text-sm text-foreground">
                  <span className="font-medium">Источник:</span>{" "}
                  <span className="text-xs font-mono">{String(link.source)}</span>
                </p>
                <p className="text-sm text-foreground">
                  <span className="font-medium">Цель:</span>{" "}
                  <span className="text-xs font-mono">{String(link.target)}</span>
                </p>
              </div>
              <div className="flex items-center gap-2">
                {link.type && (
                  <Badge variant="outline">
                    {LINK_TYPE_LABELS[link.type] ?? link.type}
                  </Badge>
                )}
                {link.label && (
                  <span className="text-xs text-muted-foreground">
                    {link.label}
                  </span>
                )}
              </div>
              {link.value > 0 && (
                <p className="text-xs text-muted-foreground">
                  Вес: {link.value}
                </p>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
