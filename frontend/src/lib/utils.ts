/**
 * Утилиты ZanAlytics.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Объединение классов Tailwind (shadcn-стандарт). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Цвет по серьёзности обнаружения. */
export function severityColor(severity: string): string {
  switch (severity) {
    case "high":
      return "text-red-500 bg-red-500/10 border-red-500/30";
    case "medium":
      return "text-amber-500 bg-amber-500/10 border-amber-500/30";
    case "low":
      return "text-emerald-500 bg-emerald-500/10 border-emerald-500/30";
    default:
      return "text-muted-foreground bg-muted";
  }
}

/** Цвет по типу документа (для графа и бэйджей). */
export function typeColor(type: string): string {
  switch (type) {
    case "code":
      return "text-blue-400 bg-blue-400/10 border-blue-400/30";
    case "law":
      return "text-emerald-400 bg-emerald-400/10 border-emerald-400/30";
    case "decree":
      return "text-violet-400 bg-violet-400/10 border-violet-400/30";
    case "resolution":
      return "text-gray-400 bg-gray-400/10 border-gray-400/30";
    case "order":
      return "text-orange-400 bg-orange-400/10 border-orange-400/30";
    case "contradiction":
      return "text-red-400 bg-red-400/10 border-red-400/30";
    case "duplication":
      return "text-amber-400 bg-amber-400/10 border-amber-400/30";
    case "outdated":
      return "text-gray-400 bg-gray-400/10 border-gray-400/30";
    default:
      return "text-muted-foreground bg-muted";
  }
}

/** Русское наименование типа. */
export function typeLabel(type: string): string {
  const labels: Record<string, string> = {
    code: "Кодекс",
    law: "Закон",
    decree: "Указ",
    resolution: "Постановление",
    order: "Приказ",
    contradiction: "Противоречие",
    duplication: "Дублирование",
    outdated: "Устаревшая норма",
    high: "Высокая",
    medium: "Средняя",
    low: "Низкая",
    active: "Действующий",
    expired: "Утратил силу",
  };
  return labels[type] ?? type;
}

/** Форматирование ISO-даты в русский формат. */
export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

/** Форматирование confidence float → "85%". */
export function confidencePercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
