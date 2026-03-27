"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Network,
  Search,
  FileText,
  Zap,
  Info,
  Scale,
  Menu,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Дашборд", icon: LayoutDashboard },
  { href: "/graph", label: "Граф", icon: Network },
  { href: "/findings", label: "Обнаружения", icon: Search },
  { href: "/documents", label: "Документы", icon: FileText },
  { href: "/analyze", label: "Анализ", icon: Zap },
  { href: "/about", label: "О системе", icon: Info },
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
        className="fixed top-3 left-3 z-50 md:hidden text-white"
        onClick={() => setCollapsed(!collapsed)}
        aria-label="Меню"
      >
        {collapsed ? <X className="size-5" /> : <Menu className="size-5" />}
      </Button>

      {/* Оверлей для мобильных */}
      {collapsed && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
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
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-[#0F172A]",
          "transition-transform duration-200 ease-in-out",
          "md:relative md:translate-x-0",
          collapsed ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        )}
      >
        {/* Логотип */}
        <div className="flex h-20 items-center gap-3 px-6 border-b border-white/[0.06]">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-600 to-amber-500 shadow-lg shadow-amber-600/20">
            <Scale className="size-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight">
              ZanAlytics
            </h1>
            <p className="text-[11px] text-slate-400">
              Анализ законодательства
            </p>
          </div>
        </div>

        {/* Навигация */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setCollapsed(false)}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-150",
                  active
                    ? "bg-white/[0.08] text-white font-medium border-l-[3px] border-amber-500 pl-[9px]"
                    : "text-slate-400 hover:bg-white/[0.04] hover:text-white border-l-[3px] border-transparent pl-[9px]",
                )}
              >
                <item.icon className={cn(
                  "size-[18px] transition-colors",
                  active ? "text-amber-400" : "text-slate-500 group-hover:text-slate-300"
                )} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Разделитель */}
        <div className="mx-4 border-t border-white/[0.06]" />

        {/* Дисклеймер */}
        <div className="p-4">
          <div className="rounded-lg bg-white/[0.03] p-3">
            <p className="text-[11px] text-slate-500 leading-relaxed">
              Анализ выполнен ИИ и требует верификации юристом
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
