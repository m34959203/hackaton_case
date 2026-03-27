import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default async function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Документ {id}</h1>
        <p className="text-sm text-muted-foreground">
          Дерево статей и связанные обнаружения
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Структура документа</CardTitle>
        </CardHeader>
        <CardContent className="flex h-64 items-center justify-center">
          <p className="text-muted-foreground">
            Дерево статей будет подключено к API
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
