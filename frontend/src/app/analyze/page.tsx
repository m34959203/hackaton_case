"use client";

import { useState, useCallback, useRef } from "react";
import { analyzeText } from "@/lib/api";
import type {
  AnalysisStepData,
  AnalysisResultData,
  AnalysisErrorData,
  AnalysisResultFinding,
  AnalysisSimilarNorm,
} from "@/lib/types";
import AnalysisForm from "@/components/analyze/AnalysisForm";
import AnalysisProgress from "@/components/analyze/AnalysisProgress";
import AnalysisResults from "@/components/analyze/AnalysisResults";

/** Шаг прогресса для отображения. */
interface ProgressStep {
  step: string;
  message: string;
  done: boolean;
}

const STEP_LABELS: Record<string, string> = {
  embedding: "Эмбеддинг",
  searching: "Поиск",
  analyzing: "Анализ ИИ",
};

export default function AnalyzePage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [steps, setSteps] = useState<ProgressStep[]>([]);
  const [resultFindings, setResultFindings] = useState<AnalysisResultFinding[]>([]);
  const [similarNorms, setSimilarNorms] = useState<AnalysisSimilarNorm[]>([]);
  const [summary, setSummary] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const handleSubmit = useCallback((text: string) => {
    /* Сброс состояния */
    setIsAnalyzing(true);
    setSteps([]);
    setResultFindings([]);
    setSimilarNorms([]);
    setSummary(null);
    setIsComplete(false);
    setError(null);

    const controller = analyzeText(text, (event) => {
      switch (event.event) {
        case "embedding":
        case "searching":
        case "analyzing": {
          const d = event.data as AnalysisStepData;
          setSteps((prev) => {
            const label = STEP_LABELS[event.event] ?? event.event;
            const existing = prev.findIndex((s) => s.step === label);
            const step: ProgressStep = {
              step: label,
              message: d.status,
              done: d.done ?? false,
            };
            if (existing >= 0) {
              const updated = [...prev];
              updated[existing] = step;
              return updated;
            }
            return [...prev, step];
          });
          break;
        }
        case "result": {
          const d = event.data as AnalysisResultData;
          setResultFindings(d.findings ?? []);
          setSimilarNorms(d.similar_norms ?? []);
          setSummary(d.summary ?? null);
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

      <AnalysisResults
        findings={resultFindings}
        similarNorms={similarNorms}
        summary={summary}
      />
    </div>
  );
}
