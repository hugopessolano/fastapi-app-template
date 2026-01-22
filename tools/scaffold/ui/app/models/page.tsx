"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
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
import {
  FieldBlock,
  HelperText,
  Section,
  Toggle,
  ToggleRow,
} from "@/components/scaffold-ui";
import { fetchJson } from "@/lib/scaffold-api";
import { useScaffoldStatus } from "@/components/scaffold-status";
import { useRequireProject } from "@/components/project-guard";

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

const fieldTypes = ["String", "Integer", "Float", "Boolean", "DateTime"];
const relationTypes = [
  { value: "belongs_to", label: "Belongs to" },
  { value: "has_many", label: "Has many" },
  { value: "many_to_many", label: "Many to many" },
];
const onDeleteOptions = [
  { value: "", label: "No action" },
  { value: "restrict", label: "Restrict" },
  { value: "cascade", label: "Cascade" },
  { value: "set null", label: "Set null" },
];

function defaultJoinTable(source: string, target: string) {
  if (!source || !target) {
    return "";
  }
  return `${source}_${target}`;
}

function defaultForeignKey(target: string) {
  if (!target) {
    return "";
  }
  return `${target.replace(/s$/, "")}_id`;
}

export default function ModelEditor() {
  const searchParams = useSearchParams();
  const { setStatus } = useScaffoldStatus();
  const activeProject = useRequireProject();
  const [specItems, setSpecItems] = useState<SpecItem[]>([]);
  const [specPath, setSpecPath] = useState("");
  const [spec, setSpec] = useState<SpecForm>(emptySpec());
  const [isBusy, setIsBusy] = useState(false);

  const existingPaths = useMemo(
    () => new Set(specItems.map((item) => item.path)),
    [specItems]
  );
  const isExisting = existingPaths.has(specPath);

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

  const targetOptions = useMemo(
    () => Array.from(new Set(specItems.map((item) => item.plural || item.name))),
    [specItems]
  );

  useEffect(() => {
    if (activeProject) {
      loadSpecs(activeProject.id);
    }
  }, [activeProject]);

  useEffect(() => {
    if (!activeProject) {
      return;
    }
    const path = searchParams.get("path");
    if (path) {
      selectSpec(path);
    }
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
      if (!activeProject) {
        return;
      }
      setSpecPath(path);
      const data = await fetchJson(`/specs/read?path=${encodeURIComponent(path)}`, {
        projectId: activeProject.id,
      });
      const normalized = normalizeSpec(data.spec ?? {});
      setSpec(normalized);
      setStatus({ tone: "success", message: "Spec loaded." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

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
        body: JSON.stringify({ path: specPath, spec }),
        projectId: activeProject.id,
      });
      const action = isExisting ? "modify" : "create";
      await fetchJson(`/scaffold/${action}`, {
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

  const updateRelation = (index: number, updates: Partial<RelationForm>) =>
    setSpec((current) => ({
      ...current,
      relations: current.relations.map((relation, idx) =>
        idx === index ? { ...relation, ...updates } : relation
      ),
    }));

  const removeRelation = (index: number) =>
    setSpec((current) => ({
      ...current,
      relations: current.relations.filter((_, idx) => idx !== index),
    }));

  const addRelation = () =>
    setSpec((current) => ({
      ...current,
      relations: [
        ...current.relations,
        {
          name: "relation",
          type: "belongs_to",
          target: "",
          foreign_key: "",
          through: "",
          back_populates: "",
          nullable: false,
          on_delete: "",
          soft_delete_cascade: false,
        },
      ],
    }));


  if (!activeProject) {
    return null;
  }

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <Button asChild variant="ghost" size="sm" className="gap-2">
          <Link href="/endpoints">
            <ArrowLeft className="h-4 w-4" />
            Volver a endpoints
          </Link>
        </Button>
      </div>

      <div className="space-y-2">
        <h1 className="text-balance text-2xl font-semibold sm:text-3xl">
          Modelos
        </h1>
        <p className="text-pretty text-sm text-muted-foreground">
          Ajusta campos, relaciones y claves foraneas sin perder consistencia.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <Card>
          <CardHeader>
            <CardTitle>Endpoints</CardTitle>
            <CardDescription>Selecciona una version para editar.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {groupedSpecs.length === 0 && (
                <div className="text-pretty rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                  No hay endpoints creados todavia.
                </div>
              )}
              {groupedSpecs.map((group) => (
                <div
                  key={group.name}
                  className="rounded-3xl border border-border/60 bg-background/60 p-4"
                >
                  <div className="text-base font-semibold text-foreground">
                    {group.name}
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
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => selectSpec(item.path)}
                        >
                          Editar
                        </Button>
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
              onClick={() => loadSpecs(activeProject.id)}
              disabled={isBusy}
            >
              Refresh list
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Editar modelo</CardTitle>
            <CardDescription>
              Guarda cambios para regenerar el codigo del modelo.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Section title="Contexto" info="Datos de referencia para el modelo actual.">
              <div className="grid gap-4 md:grid-cols-2">
                <FieldBlock label="Ruta del spec">
                  <Input value={specPath} readOnly />
                </FieldBlock>
                <FieldBlock label="Version">
                  <Input value={spec.version} readOnly />
                </FieldBlock>
                <FieldBlock label="Nombre">
                  <Input value={spec.name} readOnly />
                </FieldBlock>
                <FieldBlock label="Tabla">
                  <Input value={spec.table_name} readOnly />
                </FieldBlock>
              </div>
              <HelperText>
                Para cambiar identidad o version usa el editor principal.
              </HelperText>
            </Section>

            <Section title="Campos" info="Define las columnas base del modelo.">
              <div className="space-y-3">
                {spec.fields.map((field, index) => (
                  <div
                    key={`field-${index}`}
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

            <Section
              title="Relaciones"
              info="Define relaciones entre modelos y sus claves foraneas."
            >
              <div className="space-y-3">
                {spec.relations.map((relation, index) => (
                  <div
                    key={`relation-${index}`}
                    className="space-y-3 rounded-2xl border border-border/60 bg-background/70 p-4"
                  >
                    <div className="grid gap-3 md:grid-cols-2">
                      <FieldBlock label="Nombre">
                        <Input
                          placeholder="customer"
                          value={relation.name}
                          onChange={(event) =>
                            updateRelation(index, { name: event.target.value })
                          }
                        />
                      </FieldBlock>
                      <FieldBlock label="Tipo">
                        <select
                          value={relation.type}
                          onChange={(event) => {
                            const value = event.target.value as RelationForm["type"];
                            const updated: Partial<RelationForm> = { type: value };
                            if (value === "many_to_many" && !relation.through) {
                              updated.through = defaultJoinTable(
                                spec.table_name,
                                relation.target
                              );
                            }
                            if (value === "belongs_to" && !relation.foreign_key) {
                              updated.foreign_key = defaultForeignKey(
                                relation.target
                              );
                            }
                            updateRelation(index, updated);
                          }}
                          className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
                        >
                          {relationTypes.map((type) => (
                            <option key={type.value} value={type.value}>
                              {type.label}
                            </option>
                          ))}
                        </select>
                      </FieldBlock>
                      <FieldBlock label="Target">
                        <Input
                          list="relation-targets"
                          placeholder="customers"
                          value={relation.target}
                          onChange={(event) => {
                            const target = event.target.value;
                            const updates: Partial<RelationForm> = { target };
                            if (relation.type === "many_to_many") {
                              updates.through =
                                relation.through ||
                                defaultJoinTable(spec.table_name, target);
                            }
                            if (relation.type === "belongs_to") {
                              updates.foreign_key =
                                relation.foreign_key || defaultForeignKey(target);
                            }
                            updateRelation(index, updates);
                          }}
                        />
                      </FieldBlock>
                      <FieldBlock label="Back populates">
                        <Input
                          placeholder="sales"
                          value={relation.back_populates}
                          onChange={(event) =>
                            updateRelation(index, {
                              back_populates: event.target.value,
                            })
                          }
                        />
                      </FieldBlock>
                      {relation.type === "belongs_to" && (
                        <FieldBlock label="Foreign key">
                          <Input
                            placeholder="customer_id"
                            value={relation.foreign_key}
                            onChange={(event) =>
                              updateRelation(index, {
                                foreign_key: event.target.value,
                              })
                            }
                          />
                        </FieldBlock>
                      )}
                      {relation.type === "many_to_many" && (
                        <FieldBlock label="Join table">
                          <Input
                            placeholder="sales_products"
                            value={relation.through}
                            onChange={(event) =>
                              updateRelation(index, {
                                through: event.target.value,
                              })
                            }
                          />
                        </FieldBlock>
                      )}
                      {(relation.type === "belongs_to" ||
                        relation.type === "many_to_many") && (
                        <FieldBlock label="On delete">
                          <select
                            value={relation.on_delete}
                            onChange={(event) =>
                              updateRelation(index, {
                                on_delete: event.target.value,
                              })
                            }
                            className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
                          >
                            {onDeleteOptions.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </FieldBlock>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-4">
                      {relation.type === "belongs_to" && (
                        <ToggleRow
                          label="Nullable foreign key"
                          checked={relation.nullable}
                          onChange={(value) =>
                            updateRelation(index, { nullable: value })
                          }
                        />
                      )}
                      {relation.type === "has_many" && (
                        <ToggleRow
                          label="Soft delete cascade"
                          checked={relation.soft_delete_cascade}
                          onChange={(value) =>
                            updateRelation(index, { soft_delete_cascade: value })
                          }
                        />
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => removeRelation(index)}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              <datalist id="relation-targets">
                {targetOptions.map((target) => (
                  <option key={target} value={target} />
                ))}
              </datalist>
              <Button
                variant="secondary"
                size="sm"
                className="mt-4"
                onClick={addRelation}
              >
                Add relation
              </Button>
            </Section>

            <Section title="Acciones principales">
              <div className="flex flex-wrap gap-3">
                <Button onClick={saveAndGenerate} disabled={isBusy}>
                  Guardar cambios
                </Button>
              </div>
            </Section>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
