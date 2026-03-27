import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DocumentsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Документы</h1>
        <p className="text-sm text-muted-foreground">
          Список проанализированных нормативно-правовых актов
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Реестр НПА</CardTitle>
        </CardHeader>
        <CardContent className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">
            Таблица документов будет подключена к API
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
