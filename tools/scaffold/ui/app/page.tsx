"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
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
import { cn } from "@/lib/utils";
import { FieldBlock, HelperText, Section, ToggleRow } from "@/components/scaffold-ui";
import { Database, FileJson2 } from "lucide-react";

type SpecSummary = {
  path: string;
  name: string;
};

type SpecItem = {
  path: string;
  name: string;
  version: string;
  plural: string;
};

type FieldForm = {
  name: string;
  type: string;
  nullable: boolean;
  unique: boolean;
};

type RelationForm = {
  name: string;
  type: "belongs_to" | "has_many" | "many_to_many";
  target: string;
  foreign_key: string;
  through: string;
  back_populates: string;
  nullable: boolean;
  on_delete: string;
  soft_delete_cascade: boolean;
};

type SpecForm = {
  version: string;
  name: string;
  plural: string;
  table_name: string;
  tags: string[];
  auth_required: boolean;
  tenant_scoped: boolean;
  soft_delete: boolean;
  pagination: boolean;
  ordering: boolean;
  fields: FieldForm[];
  relations: RelationForm[];
  endpoints: {
    list: boolean;
    get: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
  };
  tests: {
    enabled: boolean;
  };
};

type StatusState = {
  tone: "idle" | "success" | "error";
  message: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_SCAFFOLD_API_URL ?? "http://127.0.0.1:8001";

const emptySpec = (): SpecForm => ({
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
  relations: [],
  endpoints: {
    list: true,
    get: true,
    create: true,
    update: true,
    delete: true,
  },
  tests: { enabled: true },
});

const normalizeSpec = (raw: Partial<SpecForm>): SpecForm => {
  const base = emptySpec();
  const endpoints = { ...base.endpoints, ...(raw.endpoints ?? {}) };
  const tests = { ...base.tests, ...(raw.tests ?? {}) };
  return {
    ...base,
    ...raw,
    tags: Array.isArray(raw.tags) ? raw.tags : base.tags,
    fields:
      Array.isArray(raw.fields) && raw.fields.length > 0
        ? raw.fields
        : base.fields,
    relations: Array.isArray(raw.relations) ? raw.relations : [],
    endpoints,
    tests,
  };
};


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

function nextVersion(versions: string[]) {
  const numbers = versions
    .map((version) => Number.parseInt(version.replace(/\D/g, ""), 10))
    .filter((value) => !Number.isNaN(value));
  const next = numbers.length > 0 ? Math.max(...numbers) + 1 : 1;
  return `v${next}`;
}

function buildVersionPath(path: string, version: string) {
  const parts = path.split("/");
  const filename = parts.pop() ?? "endpoint.json";
  const base = filename.replace(/_v\\d+\\.json$/i, "").replace(/\\.json$/i, "");
  return [...parts, `${base}_${version}.json`].join("/");
}


export default function ScaffoldStudio() {
  const [specItems, setSpecItems] = useState<SpecItem[]>([]);
  const [specPath, setSpecPath] = useState("");
  const [spec, setSpec] = useState<SpecForm>(emptySpec());
  const [tagsInput, setTagsInput] = useState(spec.tags.join(", "));
  const [status, setStatus] = useState<StatusState>({
    tone: "idle",
    message: "Ready.",
  });
  const [isBusy, setIsBusy] = useState(false);

  const existingPaths = useMemo(
    () => new Set(specItems.map((item) => item.path)),
    [specItems]
  );
  const isExisting = existingPaths.has(specPath);
  const primaryLabel = isExisting ? "Guardar cambios" : "Crear endpoint";

  const groupedSpecs = useMemo(() => {
    const groups = new Map<string, SpecItem[]>();
    specItems.forEach((item) => {
      const key = item.name || item.plural || item.path;
      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)?.push(item);
    });
    return Array.from(groups.entries()).map(([name, items]) => ({
      name,
      items: [...items].sort((a, b) => a.version.localeCompare(b.version)),
    }));
  }, [specItems]);


  const currentGroup = useMemo(() => {
    if (!specPath) {
      return null;
    }
    return groupedSpecs.find((group) =>
      group.items.some((item) => item.path === specPath)
    );
  }, [groupedSpecs, specPath]);

  useEffect(() => {
    loadSpecs();
  }, []);

  useEffect(() => {
    setTagsInput(spec.tags.join(", "));
  }, [spec.tags]);

  const loadSpecs = async () => {
    try {
      const data = await fetchJson("/specs");
      const list: SpecSummary[] = data.specs ?? [];
      const detailed = await Promise.all(
        list.map(async (item) => {
          try {
            const detail = await fetchJson(
              `/specs/read?path=${encodeURIComponent(item.path)}`
            );
            return {
              path: item.path,
              name: detail.spec.name ?? item.name,
              version: detail.spec.version ?? "v1",
              plural: detail.spec.plural ?? item.name,
            } as SpecItem;
          } catch (error) {
            setStatus({ tone: "error", message: String(error) });
            return {
              path: item.path,
              name: item.name,
              version: "v1",
              plural: item.name,
            } as SpecItem;
          }
        })
      );
      setSpecItems(detailed);
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

  const selectSpec = async (path: string) => {
    try {
      setSpecPath(path);
      const data = await fetchJson(`/specs/read?path=${encodeURIComponent(path)}`);
      const normalized = normalizeSpec(data.spec ?? {});
      setSpec(normalized);
      setTagsInput((normalized.tags ?? []).join(", "));
      setStatus({ tone: "success", message: "Spec loaded." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };


  const startNewEndpoint = () => {
    setSpecPath("");
    setSpec(emptySpec());
    setTagsInput(emptySpec().tags.join(", "));
  };

  const createNewVersion = async (base: SpecItem) => {
    try {
      setIsBusy(true);
      const data = await fetchJson(
        `/specs/read?path=${encodeURIComponent(base.path)}`
      );
      const baseSpec = normalizeSpec(data.spec ?? {});
      const versions = groupedSpecs
        .find((group) => group.name === base.name)
        ?.items.map((item) => item.version) ?? [baseSpec.version];
      const newVersion = nextVersion(versions);
      const newPath = buildVersionPath(base.path, newVersion);
      setSpecPath(newPath);
      setSpec({ ...baseSpec, version: newVersion });
      setTagsInput((baseSpec.tags ?? []).join(", "));
      setStatus({ tone: "success", message: "New version ready." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const parsedTags = useMemo(
    () =>
      tagsInput
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
    [tagsInput]
  );

  const specPayload = useMemo(
    () => ({
      ...spec,
      tags: parsedTags,
    }),
    [parsedTags, spec]
  );

  const saveAndGenerate = async () => {
    if (!specPath.trim()) {
      setStatus({ tone: "error", message: "Spec path is required." });
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson("/specs/write", {
        method: "POST",
        body: JSON.stringify({ path: specPath, spec: specPayload }),
      });
      const action = isExisting ? "modify" : "create";
      await fetchJson(`/scaffold/${action}`, {
        method: "POST",
        body: JSON.stringify({ spec_path: specPath }),
      });
      await loadSpecs();
      setStatus({ tone: "success", message: "Changes saved and generated." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };


  const runSync = async (direction: "to-code" | "from-code") => {
    if (!specPath.trim()) {
      setStatus({ tone: "error", message: "Spec path is required." });
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson(`/scaffold/sync-${direction}`, {
        method: "POST",
        body: JSON.stringify({ spec_path: specPath }),
      });
      await loadSpecs();
      setStatus({ tone: "success", message: `Sync ${direction} completed.` });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const removeSpec = async (path: string) => {
    const ok = window.confirm(
      `Delete ${path}? This removes the spec and generated code.`
    );
    if (!ok) {
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson("/scaffold/remove", {
        method: "POST",
        body: JSON.stringify({ spec_path: path, delete_spec: true }),
      });
      if (specPath === path) {
        startNewEndpoint();
      }
      await loadSpecs();
      setStatus({ tone: "success", message: "Version deleted." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const updateSpec = (updates: Partial<SpecForm>) =>
    setSpec((current) => ({ ...current, ...updates }));

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
                UX-first
              </span>
            </div>
            <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Administra endpoints y versiones con un flujo claro.
            </h1>
            <p className="max-w-2xl text-base text-muted-foreground">
              Crea, edita y versiona endpoints con formularios guiados. Cada
              cambio guarda el spec y genera el codigo automaticamente.
            </p>
          </div>
          <div className="flex w-full max-w-sm flex-col gap-3">
            <Button asChild variant="secondary">
              <Link href="/settings">Configuracion general</Link>
            </Button>
            <Card className="animate-fade-in">
              <CardHeader>
                <CardTitle>API Status</CardTitle>
                <CardDescription>
                  Connected to <span className="font-medium">{API_BASE}</span>
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
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
          <Card className="animate-fade-up">
            <CardHeader className="space-y-4">
              <div>
                <CardTitle>Endpoints</CardTitle>
                <CardDescription>
                  Selecciona una version para editar o eliminar.
                </CardDescription>
              </div>
              <Button onClick={startNewEndpoint} variant="default" size="sm">
                Nuevo endpoint
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {groupedSpecs.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                    No hay endpoints creados todavia.
                  </div>
                )}
                {groupedSpecs.map((group, index) => (
                  <div
                    key={group.name}
                    style={{ animationDelay: `${index * 60}ms` }}
                    className="animate-fade-up rounded-3xl border border-border/60 bg-background/60 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-base font-semibold text-foreground">
                          {group.name}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {group.items.length} version(es)
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => createNewVersion(group.items[0])}
                        disabled={isBusy}
                      >
                        Nueva version
                      </Button>
                    </div>
                    <div className="mt-3 space-y-2">
                      {group.items.map((item) => (
                        <div
                          key={item.path}
                          className={cn(
                            "flex items-center justify-between rounded-2xl border px-3 py-2 text-sm",
                            item.path === specPath
                              ? "border-primary/60 bg-primary/10"
                              : "border-border/60 bg-background/80"
                          )}
                        >
                          <div>
                            <div className="font-medium text-foreground">
                              {item.version}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {item.path}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => selectSpec(item.path)}
                            >
                              Editar
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => removeSpec(item.path)}
                              disabled={isBusy}
                            >
                              Eliminar
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
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
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <CardTitle>
                  {isExisting ? "Editar endpoint" : "Crear endpoint"}
                </CardTitle>
                <CardDescription>
                  {isExisting
                    ? "Guarda cambios para generar el codigo."
                    : "Define el spec y crea el endpoint."}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <IconAction
                  href={`/models?path=${encodeURIComponent(specPath)}`}
                  label="Editar modelos"
                  disabled={!specPath}
                  icon={Database}
                />
                <IconAction
                  href={`/schemas?path=${encodeURIComponent(specPath)}`}
                  label="Editar schemas"
                  disabled={!specPath}
                  icon={FileJson2}
                />
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <Section title="Identidad">
                <div className="grid gap-4 md:grid-cols-2">
                  <FieldBlock label="Ruta del spec">
                    <Input
                      placeholder="specs/my-endpoint.json"
                      value={specPath}
                      onChange={(event) => setSpecPath(event.target.value)}
                    />
                    <HelperText>
                      Ruta donde se guardara el JSON del spec.
                    </HelperText>
                  </FieldBlock>
                  <FieldBlock label="Version">
                    <Input
                      placeholder="v1"
                      value={spec.version}
                      onChange={(event) =>
                        updateSpec({ version: event.target.value })
                      }
                    />
                    {currentGroup?.items.length ? (
                      <HelperText>
                        Versiones disponibles:{" "}
                        {currentGroup.items.map((item) => item.version).join(", ")}
                      </HelperText>
                    ) : (
                      <HelperText>Define la version que deseas editar.</HelperText>
                    )}
                  </FieldBlock>
                  <FieldBlock label="Nombre">
                    <Input
                      placeholder="widget"
                      value={spec.name}
                      onChange={(event) => updateSpec({ name: event.target.value })}
                    />
                  </FieldBlock>
                  <FieldBlock label="Plural">
                    <Input
                      placeholder="widgets"
                      value={spec.plural}
                      onChange={(event) => updateSpec({ plural: event.target.value })}
                    />
                  </FieldBlock>
                  <FieldBlock label="Tabla">
                    <Input
                      placeholder="widgets"
                      value={spec.table_name}
                      onChange={(event) =>
                        updateSpec({ table_name: event.target.value })
                      }
                    />
                  </FieldBlock>
                  <FieldBlock label="Tags">
                    <Input
                      placeholder="Widgets, Catalog"
                      value={tagsInput}
                      onChange={(event) => setTagsInput(event.target.value)}
                    />
                    <HelperText>Separados por coma.</HelperText>
                  </FieldBlock>
                </div>
              </Section>

              <div className="grid gap-4 md:grid-cols-2">
                <Section title="Seguridad" info="Define si el endpoint requiere autenticacion o es multi-tenant.">
                  <ToggleRow
                    label="Auth required"
                    checked={spec.auth_required}
                    onChange={(value) =>
                      updateSpec({
                        auth_required: value,
                        tenant_scoped: value ? spec.tenant_scoped : false,
                      })
                    }
                  />
                  <ToggleRow
                    label="Tenant scoped"
                    checked={spec.tenant_scoped}
                    onChange={(value) =>
                      updateSpec({
                        tenant_scoped: value,
                        auth_required: value ? true : spec.auth_required,
                      })
                    }
                  />
                </Section>
                <Section title="Comportamiento" info="Configura soft delete, paginacion y ordenamiento.">
                  <ToggleRow
                    label="Soft delete"
                    checked={spec.soft_delete}
                    onChange={(value) => updateSpec({ soft_delete: value })}
                  />
                  <ToggleRow
                    label="Pagination"
                    checked={spec.pagination}
                    onChange={(value) => updateSpec({ pagination: value })}
                  />
                  <ToggleRow
                    label="Ordering"
                    checked={spec.ordering}
                    onChange={(value) => updateSpec({ ordering: value })}
                  />
                  <ToggleRow
                    label="Tests enabled"
                    checked={spec.tests.enabled}
                    onChange={(value) =>
                      updateSpec({ tests: { ...spec.tests, enabled: value } })
                    }
                  />
                </Section>
              </div>

              <Section title="Rutas disponibles" info="Activa o desactiva rutas CRUD para este endpoint.">
                <div className="grid gap-3 md:grid-cols-2">
                  {Object.entries(spec.endpoints).map(([key, value]) => (
                    <ToggleRow
                      key={key}
                      label={key.toUpperCase()}
                      checked={value}
                      onChange={(checked) =>
                        updateSpec({
                          endpoints: { ...spec.endpoints, [key]: checked },
                        })
                      }
                    />
                  ))}
                </div>
              </Section>

              <Section title="Acciones principales">
                <div className="flex flex-wrap gap-3">
                  <Button onClick={saveAndGenerate} disabled={isBusy}>
                    {primaryLabel}
                  </Button>
                </div>
              </Section>

              <Section
                title="Sync avanzado"
                info="Opciones de emergencia para alinear codigo y spec manualmente."
              >
                <HelperText>
                  Usa estas opciones si editaste manualmente el codigo o el spec.
                </HelperText>
                <div className="mt-3 flex flex-wrap gap-3">
                  <Button
                    variant="secondary"
                    onClick={() => runSync("to-code")}
                    disabled={isBusy}
                  >
                    Sync spec -&gt; codigo
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => runSync("from-code")}
                    disabled={isBusy}
                  >
                    Sync codigo -&gt; spec
                  </Button>
                </div>
              </Section>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}

function IconAction({
  href,
  label,
  disabled,
  icon: Icon,
}: {
  href: string;
  label: string;
  disabled: boolean;
  icon: React.ComponentType<{ className?: string }>;
}) {
  if (disabled) {
    return (
      <Button variant="ghost" size="sm" className="h-9 w-9 p-0" disabled>
        <Icon className="h-4 w-4" />
      </Button>
    );
  }
  return (
    <Button
      asChild
      variant="ghost"
      size="sm"
      className="h-9 w-9 p-0"
      aria-label={label}
      title={label}
    >
      <Link href={href}>
        <Icon className="h-4 w-4" />
      </Link>
    </Button>
  );
}
