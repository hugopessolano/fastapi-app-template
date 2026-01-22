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
  ExternalDbSpec,
  SpecForm,
  SpecItem,
  SpecSummary,
} from "@/lib/specs";
import { useScaffoldStatus } from "@/components/scaffold-status";
import { useRequireProject } from "@/components/project-guard";

type ExternalConnection = {
  name: string;
  permissions: string[];
  backend?: string;
};

const defaultExternalPermissions = ["create", "read", "update", "delete"];

export default function EndpointEditorPage() {
  const searchParams = useSearchParams();
  const { setStatus } = useScaffoldStatus();
  const activeProject = useRequireProject();
  const [specItems, setSpecItems] = useState<SpecItem[]>([]);
  const [specPath, setSpecPath] = useState("");
  const [spec, setSpec] = useState<SpecForm>(emptySpec());
  const [tagsInput, setTagsInput] = useState(spec.tags.join(", "));
  const [isBusy, setIsBusy] = useState(false);
  const [externalConnections, setExternalConnections] = useState<
    ExternalConnection[]
  >([]);

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

  const decodeParam = (value: string | null) => {
    if (!value) {
      return "";
    }
    try {
      return decodeURIComponent(value);
    } catch {
      return value;
    }
  };

  useEffect(() => {
    if (activeProject) {
      loadSpecs(activeProject.id);
      loadExternalConnections(activeProject.id);
    }
  }, [activeProject]);

  useEffect(() => {
    setTagsInput(spec.tags.join(", "));
  }, [spec.tags]);

  useEffect(() => {
    if (!activeProject) {
      return;
    }
    const path = decodeParam(searchParams.get("path"));
    const cloneFrom = decodeParam(searchParams.get("cloneFrom"));
    if (cloneFrom) {
      prepareClone(cloneFrom);
      return;
    }
    if (path) {
      selectSpec(path);
      return;
    }
    startNewEndpoint();
  }, [activeProject, searchParams]);

  const loadSpecs = async (projectId: string) => {
    try {
      const data = await fetchJson("/specs", { projectId });
      const list: SpecSummary[] = data.specs ?? [];
      const detailed = await Promise.all(
        list.map(async (item) => {
          try {
            const detail = await fetchJson(
              `/specs/read?path=${encodeURIComponent(item.path)}`,
              { projectId }
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

  const loadExternalConnections = async (projectId: string) => {
    try {
      const data = await fetchJson("/external-dbs", { projectId });
      setExternalConnections(data.connections ?? []);
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
      if (!activeProject) {
        return;
      }
      setSpecPath(path);
      const data = await fetchJson(`/specs/read?path=${encodeURIComponent(path)}`, {
        projectId: activeProject.id,
      });
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
      if (!activeProject) {
        return;
      }
      const data = await fetchJson(`/specs/read?path=${encodeURIComponent(path)}`, {
        projectId: activeProject.id,
      });
      const baseSpec = normalizeSpec(data.spec ?? {});
      const group = groupedSpecs.find((item) => item.name === baseSpec.name);
      const versions = group?.items.map((item) => item.version) ?? [baseSpec.version];
      const newVersion =
        decodeParam(searchParams.get("newVersion")) || nextVersion(versions);
      const newPath =
        decodeParam(searchParams.get("newPath")) ||
        buildVersionPath(path, newVersion);
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
    if (!activeProject) {
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson("/specs/write", {
        method: "POST",
        body: JSON.stringify({ path: specPath, spec: specPayload }),
        projectId: activeProject.id,
      });
      await fetchJson("/scaffold/sync", {
        method: "POST",
        body: JSON.stringify({ spec_path: specPath }),
        projectId: activeProject.id,
      });
      await loadSpecs(activeProject.id);
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
    if (!activeProject) {
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson(`/scaffold/sync-${direction}`, {
        method: "POST",
        body: JSON.stringify({ spec_path: specPath }),
        projectId: activeProject.id,
      });
      await loadSpecs(activeProject.id);
      setStatus({ tone: "success", message: `Sync ${direction} completed.` });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const updateSpec = (updates: Partial<SpecForm>) =>
    setSpec((current) => ({ ...current, ...updates }));

  const updateExternalDb = (index: number, updates: Partial<ExternalDbSpec>) =>
    setSpec((current) => ({
      ...current,
      external_dbs: current.external_dbs.map((entry, idx) =>
        idx === index ? { ...entry, ...updates } : entry
      ),
    }));

  const removeExternalDb = (index: number) =>
    setSpec((current) => ({
      ...current,
      external_dbs: current.external_dbs.filter((_, idx) => idx !== index),
    }));

  const addExternalDb = () => {
    const selected = new Set(spec.external_dbs.map((item) => item.name));
    const next = externalConnections.find((item) => !selected.has(item.name));
    if (!next) {
      setStatus({
        tone: "error",
        message: "No hay conexiones externas disponibles.",
      });
      return;
    }
    const nextPermissions =
      next.permissions?.length > 0 ? next.permissions : defaultExternalPermissions;
    setSpec((current) => ({
      ...current,
      external_dbs: [
        ...current.external_dbs,
        { name: next.name, permissions: [...nextPermissions] },
      ],
    }));
  };

  const availablePermissions = (name: string) => {
    const entry = externalConnections.find((item) => item.name === name);
    if (!entry || entry.permissions.length === 0) {
      return defaultExternalPermissions;
    }
    return entry.permissions;
  };

  const currentGroup = useMemo(() => {
    if (!specPath) {
      return null;
    }
    return groupedSpecs.find((group) =>
      group.items.some((item) => item.path === specPath)
    );
  }, [groupedSpecs, specPath]);

  if (!activeProject) {
    return null;
  }

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

      <Card>
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
            title="Bases externas"
            info="Agrega conexiones externas para usarlas desde la logica del endpoint."
            actions={
              <Button
                variant="secondary"
                size="sm"
                onClick={addExternalDb}
                disabled={externalConnections.length === 0}
              >
                Agregar conexion
              </Button>
            }
          >
            {externalConnections.length === 0 ? (
              <HelperText>
                No hay conexiones registradas. Crealas en Bases externas.
              </HelperText>
            ) : null}
            <div className="mt-4 space-y-3">
              {spec.external_dbs.map((entry, index) => {
                const permissions = availablePermissions(entry.name);
                return (
                  <div
                    key={`${entry.name}-${index}`}
                    className="rounded-2xl border border-border/60 bg-background/60 p-4"
                  >
                    <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                      <div className="flex flex-1 flex-col gap-3">
                        <FieldBlock label="Conexion">
                          <select
                            value={entry.name}
                            onChange={(event) => {
                              const name = event.target.value;
                              updateExternalDb(index, {
                                name,
                                permissions: [...availablePermissions(name)],
                              });
                            }}
                            className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
                          >
                            {externalConnections.map((option) => (
                              <option key={option.name} value={option.name}>
                                {option.name}
                              </option>
                            ))}
                          </select>
                        </FieldBlock>
                        <div className="grid gap-3 sm:grid-cols-2">
                          {permissions.map((perm) => (
                            <ToggleRow
                              key={`${entry.name}-${perm}`}
                              label={perm}
                              checked={entry.permissions.includes(perm)}
                              onChange={(checked) => {
                                const next = checked
                                  ? [...entry.permissions, perm]
                                  : entry.permissions.filter((item) => item !== perm);
                                updateExternalDb(index, {
                                  permissions: Array.from(new Set(next)),
                                });
                              }}
                            />
                          ))}
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeExternalDb(index)}
                      >
                        Quitar
                      </Button>
                    </div>
                  </div>
                );
              })}
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
