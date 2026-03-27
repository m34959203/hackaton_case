"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { NormBrief } from "@/lib/types";

interface NormComparisonProps {
  norm_a: NormBrief;
  norm_b: NormBrief | null;
  type: string;
}

/**
 * Сравнение двух норм бок о бок.
 * Для outdated-типа отображается только одна норма.
 */
export default function NormComparison({ norm_a: normA, norm_b: normB, type }: NormComparisonProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {/* Норма A */}
      <Card className="border-blue-500/30">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-blue-400">
            Норма A
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Документ: {normA.doc_id} | Статья {normA.article}
            {normA.paragraph ? `, п. ${normA.paragraph}` : ""}
          </p>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {normA.text}
          </p>
        </CardContent>
      </Card>

      {/* Норма B */}
      {normB ? (
        <Card className="border-orange-500/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-orange-400">
              Норма B
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              Документ: {normB.doc_id} | Статья {normB.article}
              {normB.paragraph ? `, п. ${normB.paragraph}` : ""}
            </p>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {normB.text}
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card className="flex items-center justify-center border-dashed">
          <CardContent className="py-8 text-center text-muted-foreground">
            {type === "outdated"
              ? "Для устаревших норм вторая норма не применяется"
              : "Вторая норма не указана"}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
