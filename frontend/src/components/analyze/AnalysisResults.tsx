"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { typeColor, severityColor, typeLabel, confidencePercent } from "@/lib/utils";
import type { Finding } from "@/lib/types";

interface AnalysisResultsProps {
  findings: Finding[];
}

export default function AnalysisResults({ findings }: AnalysisResultsProps) {
  if (findings.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">
          Результаты ({findings.length})
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
            <div className="flex gap-4 text-xs text-muted-foreground">
              <span>
                Норма A: ст. {f.normA.article}
                {f.normA.paragraph ? `, п. ${f.normA.paragraph}` : ""}
              </span>
              {f.normB && (
                <span>
                  Норма B: ст. {f.normB.article}
                  {f.normB.paragraph ? `, п. ${f.normB.paragraph}` : ""}
                </span>
              )}
            </div>
          </div>
        ))}

        <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
          <p className="text-xs text-amber-400">
            Анализ выполнен ИИ и требует верификации юристом
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
