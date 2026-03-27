"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalysisProgressData } from "@/lib/types";
import { Loader2 } from "lucide-react";

interface AnalysisProgressProps {
  steps: AnalysisProgressData[];
  isComplete: boolean;
  error: string | null;
}

export default function AnalysisProgress({
  steps,
  isComplete,
  error,
}: AnalysisProgressProps) {
  if (steps.length === 0 && !error) return null;

  const latestProgress = steps.length > 0 ? steps[steps.length - 1].progress : 0;
  const progressPct = Math.min(Math.round(latestProgress * 100), 100);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          {!isComplete && !error && (
            <Loader2 className="size-4 animate-spin text-blue-400" />
          )}
          Прогресс анализа
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Прогресс-бар */}
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground">{progressPct}%</p>

        {/* Шаги */}
        <div className="max-h-48 space-y-1 overflow-y-auto">
          {steps.map((step, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className="mt-0.5 size-1.5 shrink-0 rounded-full bg-blue-400" />
              <span className="text-muted-foreground">
                <span className="font-medium text-foreground">{step.step}:</span>{" "}
                {step.message}
              </span>
            </div>
          ))}
        </div>

        {error && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3">
            <p className="text-xs text-red-400">{error}</p>
          </div>
        )}

        {isComplete && !error && (
          <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3">
            <p className="text-xs text-emerald-400">Анализ завершён</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
