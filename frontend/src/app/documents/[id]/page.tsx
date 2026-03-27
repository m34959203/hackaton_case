"use client";

import { use, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getDocument, getFindings } from "@/lib/api";
import {
  typeLabel,
  typeColor,
  severityColor,
  formatDate,
  confidencePercent,
} from "@/lib/utils";
import { ArrowLeft, FileText, AlertTriangle } from "lucide-react";
import type { NormBrief } from "@/lib/types";
import Link from "next/link";

export default function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const decodedId = decodeURIComponent(id);
  const router = useRouter();

  const { data: doc, isLoading: docLoading } = useQuery({
    queryKey: ["document", decodedId],
    queryFn: () => getDocument(decodedId),
  });

  const { data: findingsData } = useQuery({
    queryKey: ["findings-for-doc", decodedId],
    queryFn: () => getFindings({ limit: 100, domain: undefined }),
    enabled: !!doc,
  });

  /* Группировка норм по статьям */
  const articleTree = useMemo(() => {
    if (!doc?.norms) return [];
    const map = new Map<number, NormBrief[]>();
    for (const norm of doc.norms) {
      const list = map.get(norm.article) ?? [];
      list.push(norm);
      map.set(norm.article, list);
    }
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [doc]);

  /* Фильтрация обнаружений по документу */
  const relatedFindings = useMemo(() => {
    if (!findingsData?.items || !decodedId) return [];
    return findingsData.items.filter(
      (f) =>
        f.normA.docId === decodedId ||
        (f.normB && f.normB.docId === decodedId),
    );
  }, [findingsData, decodedId]);

  if (docLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-96" />
        <Skeleton className="h-48" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        Документ не найден
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => router.push("/documents")}
          >
            <ArrowLeft className="size-4" />
          </Button>
          <h1 className="text-xl font-bold">{doc.title}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge className={typeColor(doc.docType)}>
            {typeLabel(doc.docType)}
          </Badge>
          <Badge variant={doc.status === "active" ? "secondary" : "outline"}>
            {typeLabel(doc.status)}
          </Badge>
          {doc.domain && (
            <span className="text-xs text-muted-foreground">
              {doc.domain}
            </span>
          )}
        </div>
      </div>

      {/* Информация */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Информация о документе</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm md:grid-cols-4">
            <div>
              <span className="text-xs text-muted-foreground">ID</span>
              <p className="font-mono text-xs">{doc.id}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Дата принятия</span>
              <p>{formatDate(doc.dateAdopted)}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Дата изменения</span>
              <p>{formatDate(doc.dateAmended)}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Принявший орган</span>
              <p>{doc.adoptingBody ?? "--"}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Юридическая сила</span>
              <p>{doc.legalForce ?? "--"}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Норм</span>
              <p>{doc.normsCount}</p>
            </div>
            <div>
              <span className="text-xs text-muted-foreground">Обнаружений</span>
              <p className={doc.findingsCount > 0 ? "text-red-400 font-medium" : ""}>
                {doc.findingsCount}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Дерево статей */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileText className="size-4" />
            Структура документа ({doc.norms?.length ?? 0} норм)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {articleTree.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Нормы не найдены
            </p>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
              {articleTree.map(([article, norms]) => (
                <div key={article} className="space-y-1">
                  <h3 className="text-sm font-semibold">
                    Статья {article}
                  </h3>
                  {norms.map((norm) => (
                    <div
                      key={norm.id}
                      className="ml-4 rounded border border-border/50 p-2"
                    >
                      <span className="text-xs text-muted-foreground">
                        {norm.paragraph ? `п. ${norm.paragraph}` : ""}
                      </span>
                      <p className="text-xs leading-relaxed line-clamp-3">
                        {norm.text}
                      </p>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Связанные обнаружения */}
      {relatedFindings.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="size-4 text-amber-400" />
              Связанные обнаружения ({relatedFindings.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {relatedFindings.map((f) => (
              <Link
                key={f.id}
                href={`/findings/${f.id}`}
                className="flex items-center gap-2 rounded-lg border border-border/50 p-3 transition-colors hover:bg-muted/30"
              >
                <Badge className={typeColor(f.type)}>
                  {typeLabel(f.type)}
                </Badge>
                <Badge className={severityColor(f.severity)}>
                  {typeLabel(f.severity)}
                </Badge>
                <span className="ml-1 flex-1 truncate text-xs">
                  {f.explanation}
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  {confidencePercent(f.confidence)}
                </span>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
