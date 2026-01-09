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
import { cn } from "@/lib/utils";

type SpecSummary = {
  path: string;
  name: string;
};

type FieldForm = {
  name: string;
  type: string;
  nullable: boolean;
  unique: boolean;
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
  endpoints: {
    list: true,
    get: true,
    create: true,
    update: true,
    delete: true,
  },
  tests: { enabled: true },
});

const fieldTypes = ["String", "Integer", "Float", "Boolean", "DateTime"];

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

const toggleClass =
  "h-4 w-4 rounded border border-input bg-background text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40";

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <input
      type="checkbox"
      checked={checked}
      onChange={(event) => onChange(event.target.checked)}
      className={toggleClass}
    />
  );
}

export default function ScaffoldStudio() {
  const [specs, setSpecs] = useState<SpecSummary[]>([]);
  const [specPath, setSpecPath] = useState("");
  const [spec, setSpec] = useState<SpecForm>(emptySpec());
  const [tagsInput, setTagsInput] = useState(spec.tags.join(", "));
  const [status, setStatus] = useState<StatusState>({
    tone: "idle",
    message: "Ready.",
  });
  const [isBusy, setIsBusy] = useState(false);

  const canRun = useMemo(() => specPath.trim().length > 0, [specPath]);

  useEffect(() => {
    loadSpecs();
  }, []);

  useEffect(() => {
    setTagsInput(spec.tags.join(", "));
  }, [spec.tags]);

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
      setSpec(data.spec);
      setTagsInput((data.spec.tags ?? []).join(", "));
      setStatus({ tone: "success", message: "Spec loaded." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
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

  const saveSpec = async () => {
    if (!canRun) {
      setStatus({ tone: "error", message: "Missing spec path." });
      return false;
    }
    try {
      setIsBusy(true);
      await fetchJson("/specs/write", {
        method: "POST",
        body: JSON.stringify({ path: specPath, spec: specPayload }),
      });
      await loadSpecs();
      setStatus({ tone: "success", message: "Spec saved." });
      return true;
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
      return false;
    } finally {
      setIsBusy(false);
    }
  };

  const runAction = async (
    action: "create" | "modify" | "sync" | "remove",
    withSave = true
  ) => {
    if (!canRun) {
      setStatus({ tone: "error", message: "Missing spec path." });
      return;
    }
    try {
      setIsBusy(true);
      if (withSave) {
        const saved = await saveSpec();
        if (!saved) {
          return;
        }
      }
      await fetchJson(`/scaffold/${action}`, {
        method: "POST",
        body: JSON.stringify({
          spec_path: specPath,
          delete_spec: action === "remove",
        }),
      });
      await loadSpecs();
      if (action === "remove") {
        setSpecPath("");
        setSpec(emptySpec());
        setTagsInput(emptySpec().tags.join(", "));
      }
      setStatus({ tone: "success", message: `Action ${action} completed.` });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const updateSpec = (updates: Partial<SpecForm>) =>
    setSpec((current) => ({ ...current, ...updates }));

  const updateField = (index: number, updates: Partial<FieldForm>) =>
    setSpec((current) => ({
      ...current,
      fields: current.fields.map((field, idx) =>
        idx === index ? { ...field, ...updates } : field
      ),
    }));

  const removeField = (index: number) =>
    setSpec((current) => ({
      ...current,
      fields: current.fields.filter((_, idx) => idx !== index),
    }));

  const addField = () =>
    setSpec((current) => ({
      ...current,
      fields: [
        ...current.fields,
        { name: "new_field", type: "String", nullable: true, unique: false },
      ],
    }));

  const confirmRemove = async (path: string) => {
    const ok = window.confirm(
      `Remove ${path}? This deletes the spec and generated code.`
    );
    if (!ok) {
      return;
    }
    setSpecPath(path);
    await runAction("remove", false);
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
              Administra endpoints con formularios claros y completos.
            </h1>
            <p className="max-w-2xl text-base text-muted-foreground">
              Edita specs con widgets dedicados, define campos y dispara acciones
              create/modify/sync/remove sin tocar JSON manualmente.
            </p>
          </div>
          <Card className="animate-fade-in w-full max-w-sm">
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

        <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
          <Card className="animate-fade-up">
            <CardHeader>
              <CardTitle>Endpoints</CardTitle>
              <CardDescription>
                Selecciona un spec para editarlo o eliminarlo.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {specs.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                    No hay specs cargados todavia.
                  </div>
                )}
                {specs.map((item, index) => (
                  <div
                    key={item.path}
                    style={{ animationDelay: `${index * 60}ms` }}
                    className={cn(
                      "animate-fade-up rounded-2xl border px-4 py-3",
                      item.path === specPath
                        ? "border-primary/60 bg-primary/10"
                        : "border-border/60 bg-background/70"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-foreground">{item.name}</div>
                        <div className="text-xs text-muted-foreground">{item.path}</div>
                      </div>
                      <Badge>Spec</Badge>
                    </div>
                    <div className="mt-3 flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => selectSpec(item.path)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => confirmRemove(item.path)}
                      >
                        Delete
                      </Button>
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
            <CardHeader>
              <CardTitle>Spec editor</CardTitle>
              <CardDescription>
                Guarda el spec y aplica acciones con los botones de abajo.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  placeholder="specs/my-resource.json"
                  value={specPath}
                  onChange={(event) => setSpecPath(event.target.value)}
                />
                <Input
                  placeholder="Version (v1)"
                  value={spec.version}
                  onChange={(event) => updateSpec({ version: event.target.value })}
                />
                <Input
                  placeholder="Name"
                  value={spec.name}
                  onChange={(event) => updateSpec({ name: event.target.value })}
                />
                <Input
                  placeholder="Plural"
                  value={spec.plural}
                  onChange={(event) => updateSpec({ plural: event.target.value })}
                />
                <Input
                  placeholder="Table name"
                  value={spec.table_name}
                  onChange={(event) => updateSpec({ table_name: event.target.value })}
                />
                <Input
                  placeholder="Tags (comma separated)"
                  value={tagsInput}
                  onChange={(event) => setTagsInput(event.target.value)}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Section title="Security">
                  <ToggleRow
                    label="Auth required"
                    checked={spec.auth_required}
                    onChange={(value) => updateSpec({ auth_required: value })}
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
                <Section title="Behavior">
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

              <Section title="Endpoints">
                <div className="grid gap-3 md:grid-cols-3">
                  {Object.entries(spec.endpoints).map(([key, value]) => (
                    <ToggleRow
                      key={key}
                      label={key}
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

              <Section title="Fields">
                <div className="space-y-3">
                  {spec.fields.map((field, index) => (
                    <div
                      key={`${field.name}-${index}`}
                      className="grid gap-3 rounded-2xl border border-border/60 bg-background/70 p-4 md:grid-cols-[2fr_1fr_1fr_1fr_auto]"
                    >
                      <Input
                        placeholder="Field name"
                        value={field.name}
                        onChange={(event) =>
                          updateField(index, { name: event.target.value })
                        }
                      />
                      <select
                        value={field.type}
                        onChange={(event) =>
                          updateField(index, { type: event.target.value })
                        }
                        className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
                      >
                        {fieldTypes.map((type) => (
                          <option key={type} value={type}>
                            {type}
                          </option>
                        ))}
                      </select>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Toggle
                          checked={field.nullable}
                          onChange={(value) =>
                            updateField(index, { nullable: value })
                          }
                        />
                        Nullable
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Toggle
                          checked={field.unique}
                          onChange={(value) => updateField(index, { unique: value })}
                        />
                        Unique
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => removeField(index)}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-4"
                  onClick={addField}
                >
                  Add field
                </Button>
              </Section>

              <Section title="Actions">
                <div className="flex flex-wrap gap-3">
                  <Button onClick={saveSpec} disabled={!canRun || isBusy}>
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
                    onClick={() => runAction("remove", false)}
                    disabled={!canRun || isBusy}
                    variant="outline"
                  >
                    Remove
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

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-border/60 bg-card/70 p-5">
      <div className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {title}
      </div>
      {children}
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 text-sm text-foreground">
      <span className="text-muted-foreground">{label}</span>
      <Toggle checked={checked} onChange={onChange} />
    </label>
  );
}
