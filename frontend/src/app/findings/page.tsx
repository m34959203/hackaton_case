"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getFindings } from "@/lib/api";
import FindingsTable from "@/components/findings/FindingsTable";
import FindingsFilters from "@/components/findings/FindingsFilters";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function FindingsPage() {
  const [page, setPage] = useState(1);
  const [type, setType] = useState("");
  const [severity, setSeverity] = useState("");
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["findings", page, type, severity],
    queryFn: () =>
      getFindings({
        page,
        limit,
        type: type || undefined,
        severity: severity || undefined,
      }),
  });

  const totalPages = data?.pages ?? 1;

  const handleReset = () => {
    setType("");
    setSeverity("");
    setPage(1);
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Обнаружения</h1>
        <p className="text-sm text-muted-foreground">
          Список выявленных противоречий, дублирований и устаревших норм
        </p>
      </div>

      <FindingsFilters
        type={type}
        severity={severity}
        onTypeChange={(v) => {
          setType(v ?? "");
          setPage(1);
        }}
        onSeverityChange={(v) => {
          setSeverity(v ?? "");
          setPage(1);
        }}
        onReset={handleReset}
      />

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">
            Таблица обнаружений
            {data && (
              <span className="ml-2 font-normal text-muted-foreground">
                ({data.total})
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FindingsTable
            findings={data?.items ?? []}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Пагинация */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="icon-sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="icon-sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
