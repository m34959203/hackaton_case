"use client";

import { useState, useCallback, useRef } from "react";
import { analyzeText } from "@/lib/api";
import type {
  AnalysisProgressData,
  AnalysisCompleteData,
  AnalysisErrorData,
  Finding,
} from "@/lib/types";
import AnalysisForm from "@/components/analyze/AnalysisForm";
import AnalysisProgress from "@/components/analyze/AnalysisProgress";
import AnalysisResults from "@/components/analyze/AnalysisResults";

export default function AnalyzePage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [steps, setSteps] = useState<AnalysisProgressData[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const handleSubmit = useCallback((text: string) => {
    /* Сброс состояния */
    setIsAnalyzing(true);
    setSteps([]);
    setFindings([]);
    setIsComplete(false);
    setError(null);

    const controller = analyzeText(text, (event) => {
      switch (event.event) {
        case "progress":
          setSteps((prev) => [...prev, event.data as AnalysisProgressData]);
          break;
        case "finding":
          setFindings((prev) => [...prev, event.data as Finding]);
          break;
        case "complete": {
          const _complete = event.data as AnalysisCompleteData;
          setIsComplete(true);
          setIsAnalyzing(false);
          break;
        }
        case "error": {
          const err = event.data as AnalysisErrorData;
          setError(err.message);
          setIsAnalyzing(false);
          break;
        }
      }
    });

    controllerRef.current = controller;
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Анализ текста</h1>
        <p className="text-sm text-muted-foreground">
          Загрузите текст нормативного акта для анализа в реальном времени
        </p>
      </div>

      <AnalysisForm onSubmit={handleSubmit} isAnalyzing={isAnalyzing} />

      <AnalysisProgress
        steps={steps}
        isComplete={isComplete}
        error={error}
      />

      <AnalysisResults findings={findings} />
    </div>
  );
}
