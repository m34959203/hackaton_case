"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Search } from "lucide-react";

interface AnalysisFormProps {
  onSubmit: (text: string) => void;
  isAnalyzing: boolean;
}

export default function AnalysisForm({ onSubmit, isAnalyzing }: AnalysisFormProps) {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (trimmed.length === 0) return;
    onSubmit(trimmed);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Текст нормативного акта</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <textarea
          className="min-h-[200px] w-full resize-y rounded-lg border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:border-ring focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
          placeholder="Вставьте текст нормативного акта для анализа на противоречия, дублирования и устаревшие нормы..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isAnalyzing}
        />
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            {text.length > 0 ? `${text.length} символов` : "Минимум 50 символов"}
          </p>
          <Button
            onClick={handleSubmit}
            disabled={isAnalyzing || text.trim().length < 50}
          >
            <Search className="mr-1.5 size-4" />
            {isAnalyzing ? "Анализ..." : "Анализировать"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
