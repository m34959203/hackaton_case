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
import { Scale, Sparkles, AlertTriangle } from "lucide-react";

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
      <Card className="border-blue-800/30 bg-gradient-to-r from-[#1E3A8A]/10 via-[#1E40AF]/5 to-transparent overflow-hidden">
        <CardContent className="py-5">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-gradient-to-br from-[#1E3A8A] to-[#1E40AF] p-2.5 shadow-lg shadow-blue-900/20">
              <Sparkles className="size-5 text-white" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-sm font-semibold tracking-tight">Сводка анализа</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                ZanAlytics проанализировал{" "}
                <span className="font-semibold text-foreground">
                  {stats.total_documents} документов
                </span>{" "}
                ({stats.total_norms.toLocaleString("ru-RU")} норм) и выявил{" "}
                <span className="font-semibold text-amber-500">
                  {stats.total_findings} проблем
                </span>
                : {contradictions} противоречий, {duplications} дублирований и{" "}
                {outdated} устаревших норм.
                {highCount > 0 && (
                  <>
                    {" "}Из них{" "}
                    <span className="font-semibold text-red-500">
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

      <Separator className="my-1 opacity-50" />

      {/* Графики: тип + серьёзность */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <FindingsByTypeChart data={stats.findings_by_type} />
        <SeverityChart data={stats.findings_by_severity} />
      </div>

      {/* Домены */}
      <div className="mt-5">
        <DomainChart data={stats.top_domains} />
      </div>

      <Separator className="my-1 opacity-50" />

      {/* Последние обнаружения */}
      <div className="mt-5">
        <RecentFindings />
      </div>
    </>
  );
}

/** Скелетон дашборда при загрузке. */
function DashboardSkeleton() {
  return (
    <>
      <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="overflow-hidden">
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-20 mb-2 bg-[#1E3A8A]/10" />
              <Skeleton className="h-8 w-16 bg-[#1E3A8A]/10" />
              <Skeleton className="mt-1 h-3 w-24 bg-[#1E3A8A]/10" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Separator className="my-4" />
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {[1, 2].map((i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-64 w-full bg-[#1E3A8A]/10" />
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
    <div className="space-y-5">
      {/* Hero-секция */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#1E3A8A] via-[#1E40AF] to-[#2563EB] p-6 shadow-xl shadow-blue-900/20">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTM2IDE4YzAtMS4xLjktMiAyLTJoMTJjMS4xIDAgMiAuOSAyIDJ2MTJjMCAxLjEtLjkgMi0yIDJIMzhjLTEuMSAwLTItLjktMi0yVjE4ek0wIDM2YzAtMS4xLjktMiAyLTJoMTJjMS4xIDAgMiAuOSAyIDJ2MTJjMCAxLjEtLjkgMi0yIDJIMmMtMS4xIDAtMi0uOS0yLTJWMzZ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-50" />
        <div className="relative flex items-center gap-5">
          <div className="rounded-2xl bg-white/10 p-4 backdrop-blur-sm ring-1 ring-white/20">
            <Scale className="size-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              ZanAlytics
            </h1>
            <p className="text-sm text-blue-100/80 mt-0.5">
              AI-анализ законодательства Республики Казахстан
            </p>
          </div>
          <div className="ml-auto hidden md:flex items-center gap-2">
            <div className="rounded-lg bg-amber-500/20 px-3 py-1.5 backdrop-blur-sm ring-1 ring-amber-400/30">
              <span className="text-xs font-medium text-amber-200">Decentrathon 5.0</span>
            </div>
          </div>
        </div>
      </div>

      {isLoading && <DashboardSkeleton />}

      {error && (
        <Card className="border-destructive/20">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="rounded-xl bg-red-500/10 p-3 mb-4">
              <AlertTriangle className="size-6 text-red-500" />
            </div>
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
