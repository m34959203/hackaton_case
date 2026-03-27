"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { StatsResponse } from "@/lib/types";

/** Карточка одной метрики. */
function StatCard({
  title,
  value,
  subtitle,
  accent,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  accent?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold ${accent ?? ""}`}>{value}</div>
        {subtitle && (
          <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}

/** 4 карточки основных метрик дашборда. */
export default function StatsCards({ stats }: { stats: StatsResponse }) {
  const coverage =
    stats.totalNorms > 0
      ? Math.round((stats.totalFindings / stats.totalNorms) * 100 * 10) / 10
      : 0;

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <StatCard
        title="Документов"
        value={stats.totalDocuments.toLocaleString("ru-RU")}
        subtitle="НПА в базе"
      />
      <StatCard
        title="Норм"
        value={stats.totalNorms.toLocaleString("ru-RU")}
        subtitle="Пунктов статей"
      />
      <StatCard
        title="Обнаружений"
        value={stats.totalFindings.toLocaleString("ru-RU")}
        subtitle="Проблем найдено"
        accent="text-amber-500"
      />
      <StatCard
        title="Покрытие анализа"
        value={`${coverage}%`}
        subtitle="Доля норм с проблемами"
      />
    </div>
  );
}
