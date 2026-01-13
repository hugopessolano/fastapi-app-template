"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Database, FileJson2, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { FieldBlock, HelperText, Section, ToggleRow } from "@/components/scaffold-ui";
import { fetchJson } from "@/lib/scaffold-api";
import {
  buildVersionPath,
  emptySpec,
  nextVersion,
  normalizeSpec,
  SpecForm,
  SpecItem,
  SpecSummary,
} from "@/lib/specs";
import { useScaffoldStatus } from "@/components/scaffold-status";

export default function EndpointEditorPage() {
  const searchParams = useSearchParams();
  const { setStatus } = useScaffoldStatus();
  const [specItems, setSpecItems] = useState<SpecItem[]>([]);
  const [specPath, setSpecPath] = useState("");
  const [spec, setSpec] = useState<SpecForm>(emptySpec());
  const [tagsInput, setTagsInput] = useState(spec.tags.join(", "));
  const [isBusy, setIsBusy] = useState(false);

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

  const existingPaths = useMemo(
    () => new Set(specItems.map((item) => item.path)),
    [specItems]
  );
  const isExisting = existingPaths.has(specPath);
  const primaryLabel = isExisting ? "Guardar cambios" : "Crear endpoint";

  useEffect(() => {
    loadSpecs();
  }, []);

  useEffect(() => {
    setTagsInput(spec.tags.join(", "));
  }, [spec.tags]);

  useEffect(() => {
    const path = searchParams.get("path") ?? "";
    const cloneFrom = searchParams.get("cloneFrom");
    if (cloneFrom) {
      prepareClone(cloneFrom);
      return;
    }
    if (path) {
      selectSpec(path);
      return;
    }
    startNewEndpoint();
  }, [searchParams]);

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
              tags: Array.isArray(detail.spec.tags) ? detail.spec.tags : [],
            } as SpecItem;
          } catch (error) {
            setStatus({ tone: "error", message: String(error) });
            return {
              path: item.path,
              name: item.name,
              version: "v1",
              plural: item.name,
              tags: [],
            } as SpecItem;
          }
        })
      );
      setSpecItems(detailed);
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

  const startNewEndpoint = () => {
    setSpecPath("");
    setSpec(emptySpec());
    setTagsInput(emptySpec().tags.join(", "));
    setStatus({ tone: "idle", message: "Ready to create a new endpoint." });
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

  const prepareClone = async (path: string) => {
    try {
      const data = await fetchJson(`/specs/read?path=${encodeURIComponent(path)}`);
      const baseSpec = normalizeSpec(data.spec ?? {});
      const group = groupedSpecs.find((item) => item.name === baseSpec.name);
      const versions = group?.items.map((item) => item.version) ?? [baseSpec.version];
      const newVersion = searchParams.get("newVersion") || nextVersion(versions);
      const newPath =
        searchParams.get("newPath") || buildVersionPath(path, newVersion);
      setSpecPath(newPath);
      setSpec({ ...baseSpec, version: newVersion });
      setTagsInput((baseSpec.tags ?? []).join(", "));
      setStatus({ tone: "success", message: "New version ready." });
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

  const updateSpec = (updates: Partial<SpecForm>) =>
    setSpec((current) => ({ ...current, ...updates }));

  const currentGroup = useMemo(() => {
    if (!specPath) {
      return null;
    }
    return groupedSpecs.find((group) =>
      group.items.some((item) => item.path === specPath)
    );
  }, [groupedSpecs, specPath]);

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <Button asChild variant="ghost" size="sm" className="gap-2">
            <Link href="/endpoints">
              <ArrowLeft className="h-4 w-4" />
              Volver a endpoints
            </Link>
          </Button>
        </div>
      </div>

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
                <HelperText>Ruta donde se guardara el JSON del spec.</HelperText>
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
            <Section
              title="Seguridad"
              info="Define si el endpoint requiere autenticacion o es multi-tenant."
            >
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
            <Section
              title="Comportamiento"
              info="Configura soft delete, paginacion y ordenamiento."
            >
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

          <Section
            title="Rutas disponibles"
            info="Activa o desactiva rutas CRUD para este endpoint."
          >
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
    </section>
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
