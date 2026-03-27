"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { typeColor, severityColor, typeLabel, confidencePercent } from "@/lib/utils";
import type { Finding } from "@/lib/types";

interface FindingCardProps {
  finding: Finding;
}

export default function FindingCard({ finding }: FindingCardProps) {
  return (
    <Link href={`/findings/${finding.id}`}>
      <Card className="transition-colors hover:bg-muted/30">
        <CardContent className="flex flex-col gap-2 p-4">
          <div className="flex items-center gap-2">
            <Badge className={typeColor(finding.type)}>
              {typeLabel(finding.type)}
            </Badge>
            <Badge className={severityColor(finding.severity)}>
              {typeLabel(finding.severity)}
            </Badge>
            <span className="ml-auto font-mono text-xs text-muted-foreground">
              {confidencePercent(finding.confidence)}
            </span>
          </div>
          <p className="line-clamp-2 text-sm">{finding.explanation}</p>
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>
              Норма A: ст. {finding.normA.article}
              {finding.normA.paragraph ? `, п. ${finding.normA.paragraph}` : ""}
            </span>
            {finding.normB && (
              <span>
                Норма B: ст. {finding.normB.article}
                {finding.normB.paragraph
                  ? `, п. ${finding.normB.paragraph}`
                  : ""}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
