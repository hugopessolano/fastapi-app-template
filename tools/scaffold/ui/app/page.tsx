"use client";

import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type SpecSummary = {
  path: string;
  name: string;
};

type StatusState = {
  tone: "idle" | "success" | "error";
  message: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_SCAFFOLD_API_URL ?? "http://127.0.0.1:8001";

const emptySpec = () => ({
  version: "v1",
  name: "resource",
  plural: "resources",
  table_name: "resources",
  tags: ["Resources"],
  auth_required: true,
  tenant_scoped: false,
  soft_delete: true,
  pagination: true,
  ordering: true,
  fields: [{ name: "name", type: "String", nullable: false, unique: false }],
  endpoints: {
    list: true,
    get: true,
    create: true,
    update: true,
    delete: true,
  },
  tests: { enabled: true },
});

async function fetchJson(path: string, options?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail ?? "Request failed");
  }
  return data;
}

export default function ScaffoldStudio() {
  const [specs, setSpecs] = useState<SpecSummary[]>([]);
  const [specPath, setSpecPath] = useState("");
  const [specText, setSpecText] = useState(
    JSON.stringify(emptySpec(), null, 2)
  );
  const [status, setStatus] = useState<StatusState>({
    tone: "idle",
    message: "Ready.",
  });
  const [isBusy, setIsBusy] = useState(false);

  const canRun = useMemo(() => specPath.trim().length > 0, [specPath]);

  useEffect(() => {
    loadSpecs();
  }, []);

  const loadSpecs = async () => {
    try {
      const data = await fetchJson("/specs");
      setSpecs(data.specs ?? []);
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

  const selectSpec = async (path: string) => {
    try {
      setSpecPath(path);
      const data = await fetchJson(`/specs/read?path=${encodeURIComponent(path)}`);
      setSpecText(JSON.stringify(data.spec, null, 2));
      setStatus({ tone: "success", message: "Spec loaded." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

  const writeSpec = async () => {
    try {
      setIsBusy(true);
      const spec = JSON.parse(specText);
      await fetchJson("/specs/write", {
        method: "POST",
        body: JSON.stringify({ path: specPath, spec }),
      });
      await loadSpecs();
      setStatus({ tone: "success", message: "Spec saved." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const runAction = async (action: "create" | "modify" | "sync" | "remove") => {
    try {
      setIsBusy(true);
      await fetchJson(`/scaffold/${action}`, {
        method: "POST",
        body: JSON.stringify({ spec_path: specPath }),
      });
      await loadSpecs();
      setStatus({ tone: "success", message: `Action ${action} completed.` });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const resetSpec = () => {
    setSpecText(JSON.stringify(emptySpec(), null, 2));
    setStatus({ tone: "success", message: "Template loaded." });
  };

  return (
    <main className="relative min-h-screen overflow-hidden px-6 py-10 sm:px-10">
      <div className="pointer-events-none absolute left-10 top-16 hidden h-24 w-24 rounded-full bg-accent/30 blur-2xl sm:block" />
      <div className="pointer-events-none absolute right-16 top-24 hidden h-32 w-32 rounded-full bg-primary/25 blur-3xl sm:block" />
      <div className="pointer-events-none absolute bottom-16 left-24 hidden h-28 w-28 rounded-full bg-secondary/40 blur-3xl sm:block" />

      <section className="mx-auto flex max-w-6xl flex-col gap-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <Badge variant="accent">Scaffold Studio</Badge>
              <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                API-first
              </span>
            </div>
            <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Administra specs, modelos y routers desde un mismo panel.
            </h1>
            <p className="max-w-2xl text-base text-muted-foreground">
              Edita specs en JSON, dispara create/modify/sync/remove y mantene el
              registry alineado con el codigo generado. Todo operando sobre el
              filesystem local.
            </p>
          </div>
          <Card className="animate-fade-in w-full max-w-sm">
            <CardHeader>
              <CardTitle>API Status</CardTitle>
              <CardDescription>
                Conectado a <span className="font-medium">{API_BASE}</span>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={cn(
                  "rounded-2xl border px-4 py-3 text-sm",
                  status.tone === "success" && "border-primary/40 bg-primary/10",
                  status.tone === "error" && "border-destructive/40 bg-destructive/10",
                  status.tone === "idle" && "border-border/60 bg-muted/40"
                )}
              >
                {status.message}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
          <Card className="animate-fade-up">
            <CardHeader>
              <CardTitle>Specs disponibles</CardTitle>
              <CardDescription>
                Selecciona un spec para editar o sincronizar.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {specs.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                    No hay specs cargados todavia.
                  </div>
                )}
                {specs.map((spec, index) => (
                  <button
                    key={spec.path}
                    type="button"
                    onClick={() => selectSpec(spec.path)}
                    style={{ animationDelay: `${index * 60}ms` }}
                    className={cn(
                      "flex w-full animate-fade-up items-center justify-between rounded-2xl border px-4 py-3 text-left text-sm transition",
                      spec.path === specPath
                        ? "border-primary/60 bg-primary/10"
                        : "border-border/60 bg-background/70 hover:border-primary/40"
                    )}
                  >
                    <div>
                      <div className="font-medium text-foreground">{spec.name}</div>
                      <div className="text-xs text-muted-foreground">{spec.path}</div>
                    </div>
                    <Badge>Spec</Badge>
                  </button>
                ))}
              </div>
              <Button
                variant="secondary"
                size="sm"
                className="mt-5 w-full"
                onClick={loadSpecs}
                disabled={isBusy}
              >
                Refresh list
              </Button>
            </CardContent>
          </Card>

          <Card className="animate-fade-up">
            <CardHeader>
              <CardTitle>Editor JSON</CardTitle>
              <CardDescription>
                Guarda el spec primero y luego ejecuta acciones del scaffold.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="specs/my-resource.json"
                value={specPath}
                onChange={(event) => setSpecPath(event.target.value)}
              />
              <Textarea
                value={specText}
                onChange={(event) => setSpecText(event.target.value)}
                className="min-h-[280px] font-mono text-xs"
              />
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={writeSpec}
                  disabled={!canRun || isBusy}
                  variant="default"
                >
                  Save spec
                </Button>
                <Button
                  onClick={() => runAction("create")}
                  disabled={!canRun || isBusy}
                  variant="secondary"
                >
                  Create
                </Button>
                <Button
                  onClick={() => runAction("modify")}
                  disabled={!canRun || isBusy}
                  variant="secondary"
                >
                  Modify
                </Button>
                <Button
                  onClick={() => runAction("sync")}
                  disabled={!canRun || isBusy}
                  variant="secondary"
                >
                  Sync
                </Button>
                <Button
                  onClick={() => runAction("remove")}
                  disabled={!canRun || isBusy}
                  variant="outline"
                >
                  Remove
                </Button>
                <Button
                  onClick={resetSpec}
                  disabled={isBusy}
                  variant="ghost"
                >
                  Load template
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}
