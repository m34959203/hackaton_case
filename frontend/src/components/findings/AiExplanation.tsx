"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { confidencePercent } from "@/lib/utils";
import { BrainCircuit } from "lucide-react";

interface AiExplanationProps {
  explanation: string;
  recommendation: string | null;
  confidence: number;
}

export default function AiExplanation({
  explanation,
  recommendation,
  confidence,
}: AiExplanationProps) {
  const confPct = Math.round(confidence * 100);
  const barColor =
    confidence >= 0.8
      ? "bg-emerald-500"
      : confidence >= 0.5
        ? "bg-amber-500"
        : "bg-red-500";
  const textColor =
    confidence >= 0.8
      ? "text-emerald-400"
      : confidence >= 0.5
        ? "text-amber-400"
        : "text-red-400";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <BrainCircuit className="size-5 text-violet-400" />
          <CardTitle className="text-sm font-medium">
            Объяснение ИИ
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Прогресс-бар уверенности */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase">
              Уверенность модели
            </span>
            <span className={`text-sm font-bold ${textColor}`}>
              {confidencePercent(confidence)}
            </span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full rounded-full ${barColor} transition-all duration-700`}
              style={{ width: `${confPct}%` }}
            />
          </div>
        </div>

        <div>
          <h4 className="mb-1 text-xs font-medium text-muted-foreground uppercase">
            Анализ
          </h4>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {explanation}
          </p>
        </div>

        {recommendation && (
          <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-4">
            <h4 className="mb-1 text-xs font-medium text-violet-400 uppercase">
              Рекомендация
            </h4>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {recommendation}
            </p>
          </div>
        )}

        <div className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
          <p className="text-xs text-amber-400">
            Анализ выполнен ИИ и требует верификации юристом. Результаты
            носят рекомендательный характер.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
