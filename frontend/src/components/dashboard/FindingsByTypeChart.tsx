"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { FindingTypeStat } from "@/lib/types";
import { typeLabel } from "@/lib/utils";

const TYPE_COLORS: Record<string, string> = {
  contradiction: "#1E3A8A",
  duplication: "#D97706",
  outdated: "#64748B",
};

interface FindingsByTypeChartProps {
  data: FindingTypeStat[];
}

/** Кольцевая (donut) диаграмма обнаружений по типу. */
export default function FindingsByTypeChart({ data }: FindingsByTypeChartProps) {
  const chartData = data.map((d) => ({
    name: typeLabel(d.type),
    value: d.count,
    fill: TYPE_COLORS[d.type] ?? "#94A3B8",
  }));

  if (chartData.length === 0) {
    return (
      <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
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
    <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
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
              paddingAngle={3}
              stroke="none"
            >
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                color: "var(--card-foreground)",
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              }}
            />
            <Legend
              formatter={(value: string) => (
                <span style={{ color: "var(--card-foreground)", fontSize: "12px" }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
