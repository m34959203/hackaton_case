"use client";

import { useRouter } from "next/navigation";
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
import { typeColor, severityColor, typeLabel, confidencePercent } from "@/lib/utils";
import type { Finding } from "@/lib/types";

interface FindingsTableProps {
  findings: Finding[];
  isLoading: boolean;
}

export default function FindingsTable({ findings, isLoading }: FindingsTableProps) {
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (findings.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-muted-foreground">
        Обнаружения не найдены
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Тип</TableHead>
          <TableHead>Серьёзность</TableHead>
          <TableHead>Уверенность</TableHead>
          <TableHead>Документ A</TableHead>
          <TableHead>Документ B</TableHead>
          <TableHead>Тема кластера</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {findings.map((f) => (
          <TableRow
            key={f.id}
            className="cursor-pointer"
            onClick={() => router.push(`/findings/${f.id}`)}
          >
            <TableCell>
              <Badge className={typeColor(f.type)}>{typeLabel(f.type)}</Badge>
            </TableCell>
            <TableCell>
              <Badge className={severityColor(f.severity)}>
                {typeLabel(f.severity)}
              </Badge>
            </TableCell>
            <TableCell className="font-mono text-xs">
              {confidencePercent(f.confidence)}
            </TableCell>
            <TableCell className="max-w-[200px] truncate text-xs">
              {f.norm_a.doc_id}
              <span className="ml-1 text-muted-foreground">
                (ст. {f.norm_a.article}
                {f.norm_a.paragraph ? `, п. ${f.norm_a.paragraph}` : ""})
              </span>
            </TableCell>
            <TableCell className="max-w-[200px] truncate text-xs">
              {f.norm_b ? (
                <>
                  {f.norm_b.doc_id}
                  <span className="ml-1 text-muted-foreground">
                    (ст. {f.norm_b.article}
                    {f.norm_b.paragraph ? `, п. ${f.norm_b.paragraph}` : ""})
                  </span>
                </>
              ) : (
                <span className="text-muted-foreground">--</span>
              )}
            </TableCell>
            <TableCell className="max-w-[180px] truncate text-xs text-muted-foreground">
              {f.cluster_topic ?? "--"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
