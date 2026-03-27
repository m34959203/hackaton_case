"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { StatsResponse } from "@/lib/types";
import { FileText, Scale, AlertTriangle, Search } from "lucide-react";
import type { LucideIcon } from "lucide-react";

/** Карточка одной метрики с иконкой и цветовым акцентом. */
function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accentColor,
  accentBg,
  borderColor,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  accentColor: string;
  accentBg: string;
  borderColor: string;
}) {
  return (
    <Card className="relative overflow-hidden transition-all duration-200 hover:shadow-lg hover:shadow-black/5 hover:-translate-y-0.5">
      <CardContent className="pt-5 pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {title}
            </p>
            <p className={`text-3xl font-bold tabular-nums ${accentColor}`}>{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
          <div className={`rounded-xl p-2.5 ${accentBg}`}>
            <Icon className={`size-5 ${accentColor}`} />
          </div>
        </div>
      </CardContent>
      {/* Цветная полоска снизу */}
      <div className={`absolute bottom-0 left-0 h-1 w-full ${borderColor}`} />
    </Card>
  );
}

/** 4 карточки основных метрик дашборда. */
export default function StatsCards({ stats }: { stats: StatsResponse }) {
  const coverage =
    stats.total_norms > 0
      ? Math.round((stats.total_findings / stats.total_norms) * 100 * 10) / 10
      : 0;

  return (
    <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
      <StatCard
        title="Документов"
        value={stats.total_documents.toLocaleString("ru-RU")}
        subtitle="НПА в базе"
        icon={FileText}
        accentColor="text-blue-500"
        accentBg="bg-blue-500/10"
        borderColor="bg-blue-500"
      />
      <StatCard
        title="Норм"
        value={stats.total_norms.toLocaleString("ru-RU")}
        subtitle="Пунктов статей"
        icon={Scale}
        accentColor="text-[#1E3A8A]"
        accentBg="bg-[#1E3A8A]/10"
        borderColor="bg-[#1E3A8A]"
      />
      <StatCard
        title="Обнаружений"
        value={stats.total_findings.toLocaleString("ru-RU")}
        subtitle="Проблем найдено"
        icon={AlertTriangle}
        accentColor="text-amber-500"
        accentBg="bg-amber-500/10"
        borderColor="bg-amber-500"
      />
      <StatCard
        title="Покрытие"
        value={`${coverage}%`}
        subtitle="Доля норм с проблемами"
        icon={Search}
        accentColor="text-emerald-500"
        accentBg="bg-emerald-500/10"
        borderColor="bg-emerald-500"
      />
    </div>
  );
}
