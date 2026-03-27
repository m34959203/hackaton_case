import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">О системе ZanAlytics</h1>
        <p className="text-sm text-muted-foreground">
          Методология и технологии
        </p>
      </div>

      <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
        <CardHeader className="bg-gradient-to-r from-[#1E3A8A] to-[#1E40AF] rounded-t-lg">
          <CardTitle className="text-white">Что это?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed pt-5">
          <p>
            ZanAlytics -- AI-система анализа законодательства Республики
            Казахстан, разработанная для хакатона Decentrathon 5.0 (Кейс 1:
            Законодательная энтропия).
          </p>
          <p>
            Система автоматически выявляет три типа проблем в нормативно-правовых
            актах:
          </p>
          <ul className="list-disc space-y-1.5 pl-5">
            <li>
              <strong className="text-foreground">Противоречия</strong> -- нормы,
              которые регулируют один вопрос по-разному
            </li>
            <li>
              <strong className="text-foreground">Дублирование</strong> -- нормы,
              повторяющие друг друга без добавочной ценности
            </li>
            <li>
              <strong className="text-foreground">Устаревшие нормы</strong> --
              ссылки на отменённые акты, устаревшие термины
            </li>
          </ul>
        </CardContent>
      </Card>

      <Separator className="opacity-50" />

      <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
        <CardHeader>
          <CardTitle>Методология</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground leading-relaxed">
          <ol className="list-decimal space-y-2.5 pl-5">
            <li>
              <strong className="text-foreground">Парсинг</strong> -- сбор НПА с
              adilet.zan.kz, разбиение на отдельные нормы (пункты статей)
            </li>
            <li>
              <strong className="text-foreground">Эмбеддинги</strong> --
              векторизация норм через nomic-embed-text для семантического поиска
            </li>
            <li>
              <strong className="text-foreground">Кластеризация</strong> -- UMAP
              + HDBSCAN для группировки тематически близких норм
            </li>
            <li>
              <strong className="text-foreground">Анализ</strong> -- LLM-as-Judge
              (qwen2.5:14b) для выявления противоречий и дублирований
            </li>
            <li>
              <strong className="text-foreground">Объяснение</strong> -- каждое
              обнаружение сопровождается обоснованием с учётом юридических
              принципов (lex posterior, lex specialis)
            </li>
          </ol>
        </CardContent>
      </Card>

      <Separator className="opacity-50" />

      <Card className="transition-all duration-200 hover:shadow-lg hover:shadow-black/5">
        <CardHeader>
          <CardTitle>Технологии</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-muted/50 p-2.5">Backend: FastAPI + SQLite + ChromaDB</div>
            <div className="rounded-lg bg-muted/50 p-2.5">Frontend: Next.js 15 + shadcn/ui</div>
            <div className="rounded-lg bg-muted/50 p-2.5">LLM: Ollama (qwen2.5:14b)</div>
            <div className="rounded-lg bg-muted/50 p-2.5">Эмбеддинги: nomic-embed-text</div>
            <div className="rounded-lg bg-muted/50 p-2.5">Граф: NetworkX + react-force-graph-3d</div>
            <div className="rounded-lg bg-muted/50 p-2.5">Визуализация: Recharts + Three.js</div>
          </div>
        </CardContent>
      </Card>

      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-xs text-amber-500">
        Анализ выполнен ИИ и требует верификации юристом. Система предназначена
        для помощи в выявлении проблем, но не заменяет профессиональную
        юридическую экспертизу.
      </div>
    </div>
  );
}
