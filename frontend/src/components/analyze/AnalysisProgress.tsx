"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CheckCircle2 } from "lucide-react";

interface ProgressStep {
  step: string;
  message: string;
  done: boolean;
}

interface AnalysisProgressProps {
  steps: ProgressStep[];
  isComplete: boolean;
  error: string | null;
}

export default function AnalysisProgress({
  steps,
  isComplete,
  error,
}: AnalysisProgressProps) {
  if (steps.length === 0 && !error) return null;

  const totalSteps = 3;
  const doneCount = steps.filter((s) => s.done).length;
  const progressPct = isComplete ? 100 : Math.round((doneCount / totalSteps) * 100);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          {!isComplete && !error && (
            <Loader2 className="size-4 animate-spin text-blue-400" />
          )}
          {isComplete && <CheckCircle2 className="size-4 text-emerald-400" />}
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
        <div className="max-h-48 space-y-1.5 overflow-y-auto">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              {step.done ? (
                <CheckCircle2 className="size-3.5 shrink-0 text-emerald-400" />
              ) : (
                <Loader2 className="size-3.5 shrink-0 animate-spin text-blue-400" />
              )}
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
