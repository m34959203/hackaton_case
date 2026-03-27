"use client";

import { usePathname } from "next/navigation";
import ModelSelector from "@/components/layout/ModelSelector";

/** Сопоставление путей и заголовков страниц. */
function getPageTitle(pathname: string): string {
  if (pathname === "/") return "Дашборд";
  if (pathname === "/graph") return "Граф связей";
  if (pathname.startsWith("/findings/")) return "Детали обнаружения";
  if (pathname === "/findings") return "Обнаружения";
  if (pathname.startsWith("/documents/")) return "Документ";
  if (pathname === "/documents") return "Документы";
  if (pathname === "/analyze") return "Анализ текста";
  if (pathname === "/about") return "О системе";
  return "ZanAlytics";
}

/** Хлебные крошки по пути. */
function getBreadcrumbs(pathname: string): string[] {
  const crumbs = ["Главная"];
  const segments = pathname.split("/").filter(Boolean);

  const labels: Record<string, string> = {
    graph: "Граф",
    findings: "Обнаружения",
    documents: "Документы",
    analyze: "Анализ",
    about: "О системе",
  };

  for (const seg of segments) {
    crumbs.push(labels[seg] ?? seg);
  }

  return crumbs;
}

export default function Header() {
  const pathname = usePathname();
  const title = getPageTitle(pathname);
  const breadcrumbs = getBreadcrumbs(pathname);

  return (
    <header className="flex h-16 items-center justify-between border-b border-border/50 bg-background/80 backdrop-blur-sm px-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        <nav className="flex items-center gap-1 text-xs text-muted-foreground">
          {breadcrumbs.map((crumb, i) => (
            <span key={i} className="flex items-center gap-1">
              {i > 0 && <span className="text-border">/</span>}
              <span>{crumb}</span>
            </span>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <ModelSelector />
        <span className="hidden sm:inline text-xs text-muted-foreground/60">Decentrathon 5.0</span>
      </div>
    </header>
  );
}
