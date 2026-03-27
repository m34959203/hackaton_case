"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { FindingTypeStat } from "@/lib/types";
import { typeLabel } from "@/lib/utils";

const TYPE_COLORS: Record<string, string> = {
  contradiction: "#ef4444",
  duplication: "#f97316",
  outdated: "#6b7280",
};

interface FindingsByTypeChartProps {
  data: FindingTypeStat[];
}

/** Кольцевая (donut) диаграмма обнаружений по типу. */
export default function FindingsByTypeChart({ data }: FindingsByTypeChartProps) {
  const chartData = data.map((d) => ({
    name: typeLabel(d.type),
    value: d.count,
    fill: TYPE_COLORS[d.type] ?? "#a1a1aa",
  }));

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">По типу обнаружения</CardTitle>
        </CardHeader>
        <CardContent className="flex h-48 items-center justify-center">
          <p className="text-sm text-muted-foreground">Нет данных</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">По типу обнаружения</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={90}
              dataKey="value"
              nameKey="name"
              paddingAngle={2}
              stroke="none"
            >
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                color: "hsl(var(--card-foreground))",
              }}
            />
            <Legend
              formatter={(value: string) => (
                <span style={{ color: "hsl(var(--card-foreground))" }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
