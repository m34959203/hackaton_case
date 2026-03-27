"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getDocuments } from "@/lib/api";
import { typeLabel, typeColor } from "@/lib/utils";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function DocumentsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [domain, setDomain] = useState("");
  const [docType, setDocType] = useState("");
  const [status, setStatus] = useState("");
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["documents", page, domain, docType, status],
    queryFn: () =>
      getDocuments({
        page,
        limit,
        domain: domain || undefined,
        docType: docType || undefined,
        status: status || undefined,
      }),
  });

  const totalPages = data?.pages ?? 1;
  const hasFilters = domain !== "" || docType !== "" || status !== "";

  const handleReset = () => {
    setDomain("");
    setDocType("");
    setStatus("");
    setPage(1);
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Документы</h1>
        <p className="text-sm text-muted-foreground">
          Список проанализированных нормативно-правовых актов
        </p>
      </div>

      {/* Фильтры */}
      <div className="flex flex-wrap items-center gap-3">
        <Select value={domain} onValueChange={(v) => { setDomain(v ?? ""); setPage(1); }}>
          <SelectTrigger>
            <SelectValue placeholder="Домен" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Труд">Труд</SelectItem>
            <SelectItem value="Налоги">Налоги</SelectItem>
            <SelectItem value="Земля">Земля</SelectItem>
            <SelectItem value="Образование">Образование</SelectItem>
            <SelectItem value="Здоровье">Здоровье</SelectItem>
          </SelectContent>
        </Select>

        <Select value={docType} onValueChange={(v) => { setDocType(v ?? ""); setPage(1); }}>
          <SelectTrigger>
            <SelectValue placeholder="Тип НПА" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="code">Кодекс</SelectItem>
            <SelectItem value="law">Закон</SelectItem>
            <SelectItem value="decree">Указ</SelectItem>
            <SelectItem value="resolution">Постановление</SelectItem>
            <SelectItem value="order">Приказ</SelectItem>
          </SelectContent>
        </Select>

        <Select value={status} onValueChange={(v) => { setStatus(v ?? ""); setPage(1); }}>
          <SelectTrigger>
            <SelectValue placeholder="Статус" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Действующий</SelectItem>
            <SelectItem value="expired">Утратил силу</SelectItem>
          </SelectContent>
        </Select>

        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={handleReset}>
            Сбросить
          </Button>
        )}
      </div>

      {/* Таблица */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">
            Реестр НПА
            {data && (
              <span className="ml-2 font-normal text-muted-foreground">
                ({data.total})
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !data || data.items.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-muted-foreground">
              Документы не найдены
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Название</TableHead>
                  <TableHead>Тип</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead>Домен</TableHead>
                  <TableHead>Нормы</TableHead>
                  <TableHead>Обнаружения</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((doc) => (
                  <TableRow
                    key={doc.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/documents/${encodeURIComponent(doc.id)}`)}
                  >
                    <TableCell className="max-w-[300px] truncate text-sm font-medium">
                      {doc.title}
                    </TableCell>
                    <TableCell>
                      <Badge className={typeColor(doc.docType)}>
                        {typeLabel(doc.docType)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={doc.status === "active" ? "secondary" : "outline"}
                      >
                        {typeLabel(doc.status)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {doc.domain ?? "--"}
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      {doc.normsCount}
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      {doc.findingsCount > 0 ? (
                        <span className="font-medium text-red-400">
                          {doc.findingsCount}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">0</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
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
