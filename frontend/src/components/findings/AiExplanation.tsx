"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
  const confColor =
    confidence >= 0.8
      ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
      : confidence >= 0.5
        ? "text-amber-400 bg-amber-400/10 border-amber-400/30"
        : "text-red-400 bg-red-400/10 border-red-400/30";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <BrainCircuit className="size-5 text-violet-400" />
          <CardTitle className="text-sm font-medium">
            Объяснение ИИ
          </CardTitle>
          <Badge className={confColor}>
            Уверенность: {confidencePercent(confidence)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="mb-1 text-xs font-medium text-muted-foreground uppercase">
            Анализ
          </h4>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {explanation}
          </p>
        </div>

        {recommendation && (
          <div>
            <h4 className="mb-1 text-xs font-medium text-muted-foreground uppercase">
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
