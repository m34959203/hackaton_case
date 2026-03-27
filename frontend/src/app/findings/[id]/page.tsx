"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getFinding } from "@/lib/api";
import { typeColor, severityColor, typeLabel, formatDate } from "@/lib/utils";
import NormComparison from "@/components/findings/NormComparison";
import AiExplanation from "@/components/findings/AiExplanation";
import { ArrowLeft, Flag } from "lucide-react";
import { useState } from "react";

export default function FindingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [reported, setReported] = useState(false);

  const { data: finding, isLoading, error, refetch } = useQuery({
    queryKey: ["finding", id],
    queryFn: () => getFinding(Number(id)),
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
        <Skeleton className="h-32" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-muted-foreground">Не удалось загрузить обнаружение</p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Повторить
        </Button>
      </div>
    );
  }

  if (!finding) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        Обнаружение не найдено
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => router.push("/findings")}
            >
              <ArrowLeft className="size-4" />
            </Button>
            <h1 className="text-2xl font-bold">
              Обнаружение #{finding.id}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={typeColor(finding.type)}>
              {typeLabel(finding.type)}
            </Badge>
            <Badge className={severityColor(finding.severity)}>
              {typeLabel(finding.severity)}
            </Badge>
            {finding.cluster_topic && (
              <span className="text-xs text-muted-foreground">
                Кластер: {finding.cluster_topic}
              </span>
            )}
            {finding.created_at && (
              <span className="text-xs text-muted-foreground">
                {formatDate(finding.created_at)}
              </span>
            )}
          </div>
        </div>
        <Button
          variant={reported ? "secondary" : "destructive"}
          size="sm"
          onClick={() => setReported(true)}
          disabled={reported}
        >
          <Flag className="mr-1.5 size-3.5" />
          {reported ? "Отмечено" : "Неверное обнаружение"}
        </Button>
      </div>

      {/* Сравнение норм */}
      <div>
        <h2 className="mb-3 text-lg font-semibold">Сравнение норм</h2>
        <NormComparison
          norm_a={finding.norm_a}
          norm_b={finding.norm_b}
          type={finding.type}
        />
      </div>

      {/* Объяснение ИИ */}
      <AiExplanation
        explanation={finding.explanation}
        recommendation={finding.recommendation}
        confidence={finding.confidence}
      />
    </div>
  );
}
