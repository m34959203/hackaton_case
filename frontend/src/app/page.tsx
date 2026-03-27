"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { useQuery } from "@tanstack/react-query";
import { getStats } from "@/lib/api";

import StatsCards from "@/components/dashboard/StatsCards";
import FindingsByTypeChart from "@/components/dashboard/FindingsByTypeChart";
import DomainChart from "@/components/dashboard/DomainChart";
import SeverityChart from "@/components/dashboard/SeverityChart";
import RecentFindings from "@/components/dashboard/RecentFindings";

import type { StatsResponse } from "@/lib/types";

/** Контент дашборда со статистикой. */
function DashboardContent({ stats }: { stats: StatsResponse }) {
  return (
    <>
      {/* Карточки метрик */}
      <StatsCards stats={stats} />

      <Separator className="my-4" />

      {/* Графики: тип + серьёзность */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <FindingsByTypeChart data={stats.findingsByType} />
        <SeverityChart data={stats.findingsBySeverity} />
      </div>

      {/* Домены */}
      <div className="mt-4">
        <DomainChart data={stats.topDomains} />
      </div>

      <Separator className="my-4" />

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
              Убедитесь, что backend запущен на порту 8001
            </p>
          </CardContent>
        </Card>
      )}

      {stats && <DashboardContent stats={stats} />}
    </div>
  );
}
