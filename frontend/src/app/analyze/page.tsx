import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyzePage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Анализ текста</h1>
        <p className="text-sm text-muted-foreground">
          Загрузите текст нормативного акта для анализа в реальном времени
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Загрузка текста</CardTitle>
        </CardHeader>
        <CardContent className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">
            Форма загрузки + SSE-прогресс будут подключены
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
