"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { useQuery } from "@tanstack/react-query";
import { getStats } from "@/lib/api";

import { Button } from "@/components/ui/button";
import StatsCards from "@/components/dashboard/StatsCards";
import FindingsByTypeChart from "@/components/dashboard/FindingsByTypeChart";
import DomainChart from "@/components/dashboard/DomainChart";
import SeverityChart from "@/components/dashboard/SeverityChart";
import RecentFindings from "@/components/dashboard/RecentFindings";
import { Scale, Sparkles } from "lucide-react";

import type { StatsResponse } from "@/lib/types";

/** Контент дашборда со статистикой. */
function DashboardContent({ stats }: { stats: StatsResponse }) {
  const highCount =
    stats.findings_by_severity.find((s) => s.severity === "high")?.count ?? 0;
  const contradictions =
    stats.findings_by_type.find((t) => t.type === "contradiction")?.count ?? 0;
  const duplications =
    stats.findings_by_type.find((t) => t.type === "duplication")?.count ?? 0;
  const outdated =
    stats.findings_by_type.find((t) => t.type === "outdated")?.count ?? 0;

  return (
    <>
      {/* Карточки метрик */}
      <StatsCards stats={stats} />

      {/* Сводка анализа */}
      <Card className="border-blue-500/20 bg-gradient-to-r from-blue-500/5 via-violet-500/5 to-transparent">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-blue-500/10 p-2">
              <Sparkles className="size-5 text-blue-400" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold">Сводка анализа</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                ZanAlytics проанализировал{" "}
                <span className="font-medium text-foreground">
                  {stats.total_documents} документов
                </span>{" "}
                ({stats.total_norms.toLocaleString("ru-RU")} норм) и выявил{" "}
                <span className="font-medium text-amber-400">
                  {stats.total_findings} проблем
                </span>
                : {contradictions} противоречий, {duplications} дублирований и{" "}
                {outdated} устаревших норм.
                {highCount > 0 && (
                  <>
                    {" "}Из них{" "}
                    <span className="font-medium text-red-400">
                      {highCount} с высокой серьёзностью
                    </span>
                    , требующих приоритетного внимания.
                  </>
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator className="my-2" />

      {/* Графики: тип + серьёзность */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <FindingsByTypeChart data={stats.findings_by_type} />
        <SeverityChart data={stats.findings_by_severity} />
      </div>

      {/* Домены */}
      <div className="mt-4">
        <DomainChart data={stats.top_domains} />
      </div>

      <Separator className="my-2" />

      {/* Последние обнаружения */}
      <div className="mt-4">
        <RecentFindings />
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
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-1 h-3 w-24" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Separator className="my-4" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {[1, 2].map((i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    retry: false,
  });

  return (
    <div className="space-y-4">
      {/* Заголовок */}
      <div className="flex items-center gap-4">
        <div className="rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 p-3 shadow-lg shadow-blue-500/20">
          <Scale className="size-7 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">ZanAlytics</h1>
          <p className="text-sm text-muted-foreground">
            AI-анализ законодательства Республики Казахстан
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
              Убедитесь, что backend запущен на порту 8001
            </p>
            <Button variant="outline" size="sm" className="mt-4" onClick={() => refetch()}>
              Повторить
            </Button>
          </CardContent>
        </Card>
      )}

      {stats && <DashboardContent stats={stats} />}
    </div>
  );
}
