import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function FindingsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Обнаружения</h1>
        <p className="text-sm text-muted-foreground">
          Список выявленных противоречий, дублирований и устаревших норм
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Таблица обнаружений</CardTitle>
        </CardHeader>
        <CardContent className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">
            Таблица с фильтрами будет подключена к API
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
