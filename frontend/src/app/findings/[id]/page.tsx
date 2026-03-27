import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default async function FindingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Обнаружение #{id}</h1>
        <p className="text-sm text-muted-foreground">
          Детали обнаружения с объяснением ИИ
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Сравнение норм</CardTitle>
          </CardHeader>
          <CardContent className="flex h-48 items-center justify-center">
            <p className="text-muted-foreground">NormComparison</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Объяснение ИИ</CardTitle>
          </CardHeader>
          <CardContent className="flex h-48 items-center justify-center">
            <p className="text-muted-foreground">AiExplanation</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
