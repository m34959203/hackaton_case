"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";

interface FindingsFiltersProps {
  type: string;
  severity: string;
  onTypeChange: (value: string | null) => void;
  onSeverityChange: (value: string | null) => void;
  onReset: () => void;
}

export default function FindingsFilters({
  type,
  severity,
  onTypeChange,
  onSeverityChange,
  onReset,
}: FindingsFiltersProps) {
  const hasFilters = type !== "" || severity !== "";

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Select value={type} onValueChange={onTypeChange}>
        <SelectTrigger>
          <SelectValue placeholder="Тип обнаружения" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="contradiction">Противоречие</SelectItem>
          <SelectItem value="duplication">Дублирование</SelectItem>
          <SelectItem value="outdated">Устаревшая норма</SelectItem>
        </SelectContent>
      </Select>

      <Select value={severity} onValueChange={onSeverityChange}>
        <SelectTrigger>
          <SelectValue placeholder="Серьёзность" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="high">Высокая</SelectItem>
          <SelectItem value="medium">Средняя</SelectItem>
          <SelectItem value="low">Низкая</SelectItem>
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={onReset}>
          Сбросить
        </Button>
      )}
    </div>
  );
}
