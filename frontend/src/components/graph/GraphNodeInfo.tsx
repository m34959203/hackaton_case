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
      <Card className="border-white/10 bg-[#0E1223]/90 backdrop-blur-xl shadow-2xl shadow-black/30">
        <CardHeader className="pb-2 flex flex-row items-start justify-between">
          <CardTitle className="text-sm text-white/90">
            {node ? "Документ" : "Связь"}
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0 text-white/60 hover:text-white">
            &times;
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          {node && (
            <>
              <p className="text-sm font-medium text-white leading-snug">
                {node.name}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {node.group && (
                  <Badge variant="outline" className="border-white/20 text-white/80">
                    {GROUP_LABELS[node.group] ?? node.group}
                  </Badge>
                )}
                {node.status && (
                  <Badge variant={node.status === "active" ? "secondary" : "outline"} className="border-white/20 text-white/80">
                    {typeLabel(node.status)}
                  </Badge>
                )}
              </div>
              {node.domain && (
                <p className="text-xs text-white/50">
                  {node.domain}
                </p>
              )}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-white/40">Норм:</span>{" "}
                  <span className="font-medium text-white/80">{node.val}</span>
                </div>
                <div>
                  <span className="text-white/40">Обнаружений:</span>{" "}
                  <span className={node.findingsCount > 0 ? "font-medium text-red-400" : "font-medium text-white/80"}>
                    {node.findingsCount}
                  </span>
                </div>
              </div>
              <p className="text-xs text-white/40 font-mono">
                ID: {node.id}
              </p>
              <Link
                href={`/documents/${encodeURIComponent(node.id)}`}
                className="inline-block text-xs text-blue-400 hover:text-blue-300 hover:underline mt-1 transition-colors"
              >
                Открыть документ
              </Link>
            </>
          )}
          {link && (
            <>
              <div className="space-y-1">
                <p className="text-sm text-white/80">
                  <span className="font-medium text-white/90">Источник:</span>{" "}
                  <span className="text-xs font-mono text-white/60">{String(link.source)}</span>
                </p>
                <p className="text-sm text-white/80">
                  <span className="font-medium text-white/90">Цель:</span>{" "}
                  <span className="text-xs font-mono text-white/60">{String(link.target)}</span>
                </p>
              </div>
              <div className="flex items-center gap-2">
                {link.type && (
                  <Badge variant="outline" className="border-white/20 text-white/80">
                    {LINK_TYPE_LABELS[link.type] ?? link.type}
                  </Badge>
                )}
                {link.label && (
                  <span className="text-xs text-white/50">
                    {link.label}
                  </span>
                )}
              </div>
              {link.value > 0 && (
                <p className="text-xs text-white/50">
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
