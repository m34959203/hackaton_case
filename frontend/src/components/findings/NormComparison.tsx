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
    <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
      {/* Норма A -- Navy accent */}
      <Card className="border-l-4 border-l-[#1E3A8A] border-[#1E3A8A]/20 transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-blue-500">
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
          <div className="rounded-lg bg-[#1E3A8A]/5 p-3.5 border border-[#1E3A8A]/10">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {normA.text}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Норма B -- Gold accent */}
      {normB ? (
        <Card className="border-l-4 border-l-amber-600 border-amber-600/20 transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-amber-500">
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
            <div className="rounded-lg bg-amber-500/5 p-3.5 border border-amber-500/10">
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {normB.text}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="flex items-center justify-center border-dashed border-border/50">
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
