"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { typeColor, severityColor, typeLabel, confidencePercent } from "@/lib/utils";
import type { AnalysisResultFinding, AnalysisSimilarNorm } from "@/lib/types";

interface AnalysisResultsProps {
  findings: AnalysisResultFinding[];
  similarNorms: AnalysisSimilarNorm[];
  summary: string | null;
}

export default function AnalysisResults({ findings, similarNorms, summary }: AnalysisResultsProps) {
  if (findings.length === 0 && !summary) return null;

  return (
    <div className="space-y-4">
      {/* Сводка */}
      {summary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Сводка анализа</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{summary}</p>
          </CardContent>
        </Card>
      )}

      {/* Обнаружения */}
      {findings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Обнаружения ({findings.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {findings.map((f, i) => (
              <div
                key={i}
                className="rounded-lg border border-border p-3 space-y-2"
              >
                <div className="flex items-center gap-2">
                  <Badge className={typeColor(f.type)}>
                    {typeLabel(f.type)}
                  </Badge>
                  <Badge className={severityColor(f.severity)}>
                    {typeLabel(f.severity)}
                  </Badge>
                  <span className="ml-auto font-mono text-xs text-muted-foreground">
                    {confidencePercent(f.confidence)}
                  </span>
                </div>
                <p className="text-sm">{f.explanation}</p>
                {f.related_norm_id && (
                  <p className="text-xs text-muted-foreground">
                    Связанная норма: {f.related_norm_id}
                  </p>
                )}
              </div>
            ))}

            <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
              <p className="text-xs text-amber-400">
                Анализ выполнен ИИ и требует верификации юристом
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Похожие нормы */}
      {similarNorms.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Похожие нормы в базе ({similarNorms.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {similarNorms.map((n) => (
              <div
                key={n.id}
                className="rounded-lg border border-border p-3 space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-blue-400">
                    {n.doc_title}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    Сходство: {Math.round(n.similarity * 100)}%
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Ст. {n.article}{n.paragraph ? `, п. ${n.paragraph}` : ""}
                </p>
                <p className="text-sm line-clamp-3">{n.text}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
