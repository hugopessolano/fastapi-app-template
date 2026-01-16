"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Database,
  FileJson2,
  LayoutGrid,
  Menu,
  ServerCog,
  Settings,
  Waypoints,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/scaffold-api";
import { useScaffoldStatus } from "@/components/scaffold-status";

type NavItem = {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
};

const navItems: NavItem[] = [
  { label: "Endpoints", href: "/endpoints", icon: LayoutGrid },
  { label: "Models", href: "/models", icon: Database },
  { label: "Schemas", href: "/schemas", icon: FileJson2 },
  { label: "BD Externas", href: "/external-dbs", icon: Waypoints },
  { label: "Configuraciones", href: "/settings", icon: Settings },
];

const collapsedKey = "scaffold.sidebar.collapsed";

export default function ScaffoldShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { status } = useScaffoldStatus();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(collapsedKey);
    if (stored === "true") {
      setCollapsed(true);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(collapsedKey, String(collapsed));
  }, [collapsed]);

  const activeHref = useMemo(() => {
    if (pathname.startsWith("/endpoints")) return "/endpoints";
    if (pathname.startsWith("/models")) return "/models";
    if (pathname.startsWith("/schemas")) return "/schemas";
    if (pathname.startsWith("/external-dbs")) return "/external-dbs";
    if (pathname.startsWith("/settings")) return "/settings";
    return "/endpoints";
  }, [pathname]);

  return (
    <div className="relative min-h-dvh">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-10 flex h-dvh flex-col border-r border-border/60 bg-background/80 px-3 backdrop-blur",
          collapsed ? "w-16" : "w-64"
        )}
        style={{
          paddingTop: "calc(1rem + env(safe-area-inset-top))",
          paddingBottom: "calc(1rem + env(safe-area-inset-bottom))",
        }}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex size-9 items-center justify-center rounded-2xl bg-primary/20 text-primary">
              <ServerCog className="size-4" />
            </span>
            {!collapsed && (
              <span className="text-balance text-sm font-semibold text-foreground">
                Scaffold
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed((current) => !current)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="size-8"
          >
            <Menu className="size-4" />
          </Button>
        </div>

        <nav className="mt-6 flex flex-1 flex-col gap-2 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = activeHref === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-2xl px-3 py-2 text-sm",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
                title={collapsed ? item.label : undefined}
              >
                <Icon className="size-4" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        <div
          className={cn(
            "rounded-2xl border border-border/60 bg-muted/30 p-3 text-xs",
            collapsed ? "text-center" : "text-left"
          )}
        >
          {!collapsed && (
            <div className="mb-2 text-[10px] uppercase text-muted-foreground">
              API Status
            </div>
          )}
          <div className="flex items-center gap-2 text-muted-foreground">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                status.tone === "success" && "bg-primary",
                status.tone === "error" && "bg-destructive",
                status.tone === "idle" && "bg-muted-foreground/60"
              )}
            />
            {!collapsed && (
              <span className="line-clamp-2 text-xs">{status.message}</span>
            )}
          </div>
          {!collapsed && (
            <div className="mt-2 text-[10px] text-muted-foreground">
              {API_BASE}
            </div>
          )}
        </div>
      </aside>

      <main
        className={cn(
          "relative flex-1 overflow-hidden px-6 py-8 sm:px-10",
          collapsed ? "ml-16" : "ml-64"
        )}
      >
        <div className="pointer-events-none absolute left-10 top-12 hidden h-24 w-24 rounded-full bg-accent/30 blur-2xl sm:block" />
        <div className="pointer-events-none absolute right-16 top-20 hidden h-32 w-32 rounded-full bg-primary/25 blur-3xl sm:block" />
        <div className="pointer-events-none absolute bottom-16 left-24 hidden h-28 w-28 rounded-full bg-secondary/40 blur-3xl sm:block" />
        <div className="relative z-10">{children}</div>
      </main>
    </div>
  );
}
