"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Дашборд", icon: "📊" },
  { href: "/graph", label: "Граф", icon: "🔗" },
  { href: "/findings", label: "Обнаружения", icon: "🔍" },
  { href: "/documents", label: "Документы", icon: "📄" },
  { href: "/analyze", label: "Анализ", icon: "⚡" },
  { href: "/about", label: "О системе", icon: "ℹ️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  function isActive(href: string): boolean {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  }

  return (
    <>
      {/* Мобильная кнопка */}
      <Button
        variant="ghost"
        size="sm"
        className="fixed top-3 left-3 z-50 md:hidden"
        onClick={() => setCollapsed(!collapsed)}
        aria-label="Меню"
      >
        <span className="text-xl">{collapsed ? "✕" : "☰"}</span>
      </Button>

      {/* Оверлей для мобильных */}
      {collapsed && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setCollapsed(false)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setCollapsed(false);
          }}
          role="button"
          tabIndex={0}
          aria-label="Закрыть меню"
        />
      )}

      {/* Сайдбар */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-sidebar",
          "transition-transform duration-200 ease-in-out",
          "md:relative md:translate-x-0",
          collapsed ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        )}
      >
        {/* Логотип */}
        <div className="flex h-16 items-center gap-3 px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-sm">
            ZA
          </div>
          <div>
            <h1 className="text-sm font-semibold text-sidebar-foreground">
              ZanAlytics
            </h1>
            <p className="text-xs text-muted-foreground">
              Анализ законодательства
            </p>
          </div>
        </div>

        <Separator />

        {/* Навигация */}
        <nav className="flex-1 space-y-1 p-3">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setCollapsed(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive(item.href)
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
              )}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <Separator />

        {/* Дисклеймер */}
        <div className="p-4">
          <p className="text-xs text-muted-foreground leading-relaxed">
            Анализ выполнен ИИ и требует верификации юристом
          </p>
        </div>
      </aside>
    </>
  );
}
