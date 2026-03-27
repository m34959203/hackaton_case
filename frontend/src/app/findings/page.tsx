"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getFindings } from "@/lib/api";
import FindingsTable from "@/components/findings/FindingsTable";
import FindingsFilters from "@/components/findings/FindingsFilters";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

export default function FindingsPage() {
  const [page, setPage] = useState(1);
  const [type, setType] = useState("");
  const [severity, setSeverity] = useState("");
  const limit = 20;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["findings", page, type, severity],
    queryFn: () =>
      getFindings({
        page,
        limit,
        type: type || undefined,
        severity: severity || undefined,
      }),
    retry: false,
  });

  const totalPages = data ? Math.ceil(data.total / data.limit) : 1;

  const handleReset = () => {
    setType("");
    setSeverity("");
    setPage(1);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-gradient-to-br from-[#1E3A8A] to-[#1E40AF] p-2.5 shadow-lg shadow-blue-900/20">
          <Search className="size-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Обнаружения</h1>
          <p className="text-sm text-muted-foreground">
            Список выявленных противоречий, дублирований и устаревших норм
          </p>
        </div>
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

      {error && (
        <Card className="border-destructive/20">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground">Не удалось загрузить обнаружения</p>
            <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
              Повторить
            </Button>
          </CardContent>
        </Card>
      )}

      {!error && (
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
      )}

      {/* Пагинация */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="icon-sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="transition-all duration-150 hover:bg-[#1E3A8A]/10"
          >
            <ChevronLeft className="size-4" />
          </Button>
          <span className="text-sm tabular-nums text-muted-foreground">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="icon-sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="transition-all duration-150 hover:bg-[#1E3A8A]/10"
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
