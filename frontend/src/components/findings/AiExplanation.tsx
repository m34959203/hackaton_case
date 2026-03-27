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

  /* Gradient confidence bar: red -> amber -> green */
  const barGradient =
    confidence >= 0.8
      ? "bg-gradient-to-r from-emerald-600 to-emerald-400"
      : confidence >= 0.5
        ? "bg-gradient-to-r from-amber-600 to-amber-400"
        : "bg-gradient-to-r from-red-600 to-red-400";

  const textColor =
    confidence >= 0.8
      ? "text-emerald-500"
      : confidence >= 0.5
        ? "text-amber-500"
        : "text-red-500";

  return (
    <Card className="overflow-hidden transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
      {/* Navy header */}
      <CardHeader className="bg-gradient-to-r from-[#1E3A8A] to-[#1E40AF] pb-3 pt-4">
        <div className="flex items-center gap-2.5">
          <BrainCircuit className="size-5 text-white/80" />
          <CardTitle className="text-sm font-medium text-white">
            Объяснение ИИ
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-5">
        {/* Прогресс-бар уверенности */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Уверенность модели
            </span>
            <span className={`text-sm font-bold tabular-nums ${textColor}`}>
              {confidencePercent(confidence)}
            </span>
          </div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full rounded-full ${barGradient} transition-all duration-700`}
              style={{ width: `${confPct}%` }}
            />
          </div>
        </div>

        <div>
          <h4 className="mb-1.5 text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Анализ
          </h4>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {explanation}
          </p>
        </div>

        {recommendation && (
          <div className="rounded-lg border border-[#1E3A8A]/20 bg-[#1E3A8A]/5 p-4">
            <h4 className="mb-1.5 text-xs font-medium text-blue-500 uppercase tracking-wider">
              Рекомендация
            </h4>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {recommendation}
            </p>
          </div>
        )}

        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
          <p className="text-xs text-amber-500">
            Анализ выполнен ИИ и требует верификации юристом. Результаты
            носят рекомендательный характер.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
