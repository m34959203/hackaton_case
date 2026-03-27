import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function GraphPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Граф связей</h1>
        <p className="text-sm text-muted-foreground">
          3D-визуализация связей между нормативно-правовыми актами
        </p>
      </div>
      <Card className="h-[calc(100vh-14rem)]">
        <CardHeader>
          <CardTitle className="text-sm">Интерактивный граф</CardTitle>
        </CardHeader>
        <CardContent className="flex h-full items-center justify-center">
          <p className="text-muted-foreground">
            Граф будет подключён (react-force-graph-3d)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
