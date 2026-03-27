"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { FindingSeverityStat } from "@/lib/types";
import { typeLabel } from "@/lib/utils";

const SEVERITY_COLORS: Record<string, string> = {
  high: "#DC2626",
  medium: "#D97706",
  low: "#059669",
};

interface SeverityChartProps {
  data: FindingSeverityStat[];
}

/** Столбчатая диаграмма распределения обнаружений по серьёзности. */
export default function SeverityChart({ data }: SeverityChartProps) {
  const chartData = data.map((d) => ({
    name: typeLabel(d.severity),
    value: d.count,
    severity: d.severity,
  }));

  if (chartData.length === 0) {
    return (
      <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
        <CardHeader>
          <CardTitle className="text-sm">По серьёзности</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center">
          <p className="text-sm text-muted-foreground">Нет данных</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
      <CardHeader>
        <CardTitle className="text-sm">По серьёзности</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <XAxis
              dataKey="name"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
            />
            <YAxis
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                color: "var(--card-foreground)",
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              }}
              formatter={(value) => [String(value), "Обнаружений"]}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={SEVERITY_COLORS[entry.severity] ?? "#94A3B8"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
