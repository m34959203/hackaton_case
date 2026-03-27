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
      <Card>
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
    <Card>
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
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey="domain"
              width={180}
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                color: "hsl(var(--card-foreground))",
              }}
              formatter={(value, name) => {
                const label = name === "findings" ? "Обнаружений" : "Норм";
                return [String(value), label];
              }}
            />
            <Bar dataKey="norms" fill="#6366f1" radius={[0, 4, 4, 0]} name="norms" />
            <Bar dataKey="findings" fill="#ef4444" radius={[0, 4, 4, 0]} name="findings" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
