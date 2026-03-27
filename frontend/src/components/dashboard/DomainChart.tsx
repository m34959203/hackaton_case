"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { DomainStat } from "@/lib/types";

interface DomainChartProps {
  data: DomainStat[];
}

/** Столбчатая диаграмма: топ-10 доменов по количеству обнаружений. */
export default function DomainChart({ data }: DomainChartProps) {
  /* Обрезаем длинные названия доменов для оси Y */
  const chartData = data.slice(0, 10).map((d) => ({
    domain: d.domain.length > 40 ? d.domain.slice(0, 37) + "..." : d.domain,
    fullDomain: d.domain,
    findings: d.findings_count,
    norms: d.norms_count,
  }));

  if (chartData.length === 0) {
    return (
      <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
        <CardHeader>
          <CardTitle className="text-sm">Топ доменов по обнаружениям</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center">
          <p className="text-sm text-muted-foreground">Данные появятся после анализа</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
      <CardHeader>
        <CardTitle className="text-sm">Топ доменов по нормам</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ left: 20, right: 20, top: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
            <XAxis type="number" tick={{ fill: "var(--muted-foreground)", fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey="domain"
              width={180}
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                color: "var(--card-foreground)",
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              }}
              formatter={(value, name) => {
                const label = name === "findings" ? "Обнаружений" : "Норм";
                return [String(value), label];
              }}
            />
            <Bar dataKey="norms" fill="#1E3A8A" radius={[0, 6, 6, 0]} name="norms" />
            <Bar dataKey="findings" fill="#D97706" radius={[0, 6, 6, 0]} name="findings" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
