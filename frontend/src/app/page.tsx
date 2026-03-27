"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useQuery } from "@tanstack/react-query";
import { getStats } from "@/lib/api";
import { typeLabel, typeColor, severityColor, confidencePercent } from "@/lib/utils";
import type { StatsResponse } from "@/lib/types";

/** Карточка метрики. */
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

/** Плейсхолдер для графиков. */
function ChartPlaceholder({ title }: { title: string }) {
  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex h-48 items-center justify-center">
        <p className="text-sm text-muted-foreground">
          График будет подключён к API
        </p>
      </CardContent>
    </Card>
  );
}

/** Плейсхолдер недавних обнаружений. */
function RecentFindingsPlaceholder() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Последние обнаружения</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

/** Контент дашборда со статистикой. */
function DashboardContent({ stats }: { stats: StatsResponse }) {
  return (
    <>
      {/* Метрики */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          title="Документов"
          value={stats.documentsCount}
          subtitle="НПА в базе"
        />
        <StatCard
          title="Норм"
          value={stats.normsCount}
          subtitle="Пунктов статей"
        />
        <StatCard
          title="Обнаружений"
          value={stats.findingsCount}
          subtitle="Проблем найдено"
          accent="text-amber-500"
        />
        <StatCard
          title="Ср. уверенность"
          value={confidencePercent(stats.avgConfidence)}
          subtitle="Модели ИИ"
        />
      </div>

      <Separator className="my-4" />

      {/* Детализация по типам */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">По типу обнаружения</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              { type: "contradiction", count: stats.contradictions },
              { type: "duplication", count: stats.duplications },
              { type: "outdated", count: stats.outdated },
            ].map(({ type, count }) => (
              <div key={type} className="flex items-center justify-between">
                <Badge variant="outline" className={typeColor(type)}>
                  {typeLabel(type)}
                </Badge>
                <span className="text-sm font-semibold">{count}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">По серьёзности</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              { sev: "high", count: stats.highSeverity },
              { sev: "medium", count: stats.mediumSeverity },
              { sev: "low", count: stats.lowSeverity },
            ].map(({ sev, count }) => (
              <div key={sev} className="flex items-center justify-between">
                <Badge variant="outline" className={severityColor(sev)}>
                  {typeLabel(sev)}
                </Badge>
                <span className="text-sm font-semibold">{count}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">По отраслям</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(stats.domains).length > 0 ? (
              Object.entries(stats.domains)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([domain, count]) => (
                  <div
                    key={domain}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm text-muted-foreground">
                      {domain}
                    </span>
                    <span className="text-sm font-semibold">{count}</span>
                  </div>
                ))
            ) : (
              <p className="text-sm text-muted-foreground">
                Данные появятся после анализа
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Separator className="my-4" />

      {/* Графики и последние обнаружения */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <ChartPlaceholder title="Распределение по типам" />
        <ChartPlaceholder title="Динамика обнаружений" />
      </div>

      <div className="mt-4">
        <RecentFindingsPlaceholder />
      </div>
    </>
  );
}

/** Скелетон дашборда при загрузке. */
function DashboardSkeleton() {
  return (
    <>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-20" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Separator className="my-4" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    retry: false,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Панель управления</h1>
          <p className="text-sm text-muted-foreground">
            Обзор анализа законодательства Республики Казахстан
          </p>
        </div>
      </div>

      {isLoading && <DashboardSkeleton />}

      {error && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-medium text-muted-foreground">
              Не удалось загрузить данные
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Убедитесь, что backend запущен на порту 8000
            </p>
          </CardContent>
        </Card>
      )}

      {stats && <DashboardContent stats={stats} />}
    </div>
  );
}
