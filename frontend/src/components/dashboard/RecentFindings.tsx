"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useQuery } from "@tanstack/react-query";
import { getFindings } from "@/lib/api";
import { typeLabel, typeColor, severityColor, confidencePercent } from "@/lib/utils";
import Link from "next/link";

/** Список последних 5 обнаружений. */
export default function RecentFindings() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["findings", "recent"],
    queryFn: () => getFindings({ page: 1, limit: 5 }),
    retry: false,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Последние обнаружения</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-lg bg-[#1E3A8A]/10" />
              <div className="flex-1 space-y-1">
                <Skeleton className="h-4 w-3/4 bg-[#1E3A8A]/10" />
                <Skeleton className="h-3 w-1/2 bg-[#1E3A8A]/10" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Последние обнаружения</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Данные появятся после анализа
          </p>
        </CardContent>
      </Card>
    );
  }

  const findings = data.items;

  if (findings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Последние обнаружения</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Обнаружений пока нет. Запустите анализ.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Последние обнаружения</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {findings.map((f) => (
          <Link
            key={f.id}
            href={`/findings/${f.id}`}
            className="block rounded-lg border border-border/50 p-3 transition-all duration-150 hover:bg-muted/30 hover:border-border hover:shadow-sm"
          >
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={typeColor(f.type)}>
                  {typeLabel(f.type)}
                </Badge>
                <Badge variant="outline" className={severityColor(f.severity)}>
                  {typeLabel(f.severity)}
                </Badge>
                <span className="text-xs tabular-nums text-muted-foreground">
                  {confidencePercent(f.confidence)}
                </span>
              </div>
              <p className="text-sm text-foreground line-clamp-2">
                {f.explanation}
              </p>
              {f.norm_a && (
                <p className="text-xs text-muted-foreground truncate">
                  Ст. {f.norm_a.article}
                  {f.norm_a.paragraph ? `, п. ${f.norm_a.paragraph}` : ""} --{" "}
                  {f.norm_a.text.slice(0, 100)}...
                </p>
              )}
            </div>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
