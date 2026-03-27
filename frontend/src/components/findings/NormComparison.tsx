"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { NormBrief } from "@/lib/types";

interface NormComparisonProps {
  norm_a: NormBrief;
  norm_b: NormBrief | null;
  type: string;
  /** Названия документов (опционально, если доступны). */
  doc_a_title?: string;
  doc_b_title?: string;
}

/**
 * Сравнение двух норм бок о бок.
 * Для outdated-типа отображается только одна норма.
 */
export default function NormComparison({
  norm_a: normA,
  norm_b: normB,
  type,
  doc_a_title,
  doc_b_title,
}: NormComparisonProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {/* Норма A */}
      <Card className="border-l-4 border-l-blue-500 border-blue-500/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-blue-400">
            Норма A
          </CardTitle>
          {doc_a_title && (
            <p className="text-xs font-medium text-foreground">
              {doc_a_title}
            </p>
          )}
          <p className="text-xs text-muted-foreground">
            Документ: {normA.doc_id} | Статья {normA.article}
            {normA.paragraph ? `, п. ${normA.paragraph}` : ""}
          </p>
        </CardHeader>
        <CardContent>
          <div className="rounded-md bg-blue-500/5 p-3">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {normA.text}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Норма B */}
      {normB ? (
        <Card className="border-l-4 border-l-orange-500 border-orange-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-orange-400">
              Норма B
            </CardTitle>
            {doc_b_title && (
              <p className="text-xs font-medium text-foreground">
                {doc_b_title}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              Документ: {normB.doc_id} | Статья {normB.article}
              {normB.paragraph ? `, п. ${normB.paragraph}` : ""}
            </p>
          </CardHeader>
          <CardContent>
            <div className="rounded-md bg-orange-500/5 p-3">
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {normB.text}
              </p>
            </div>
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
