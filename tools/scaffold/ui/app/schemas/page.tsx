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
import {
  FieldBlock,
  HelperText,
  InfoTip,
  Section,
  Toggle,
} from "@/components/scaffold-ui";

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

type SchemaConstraintForm = {
  min_length: string;
  max_length: string;
  pattern: string;
  ge: string;
  le: string;
  gt: string;
  lt: string;
  min_items: string;
  max_items: string;
};

type SchemaFieldForm = {
  name: string;
  type: string;
  required: boolean;
  enabled: boolean;
  defaultValue: string;
  description: string;
  example: string;
  constraints: SchemaConstraintForm;
  source: "model" | "custom";
};

type SchemaRelationForm = {
  name: string;
  mode: "embedded" | "ids" | "omit";
};

type SchemaVariantForm = {
  fields: SchemaFieldForm[];
  relations: SchemaRelationForm[];
};

type CustomSchemaForm = {
  name: string;
  fields: SchemaFieldForm[];
};

type SchemaSpecForm = {
  create: SchemaVariantForm;
  update: SchemaVariantForm;
  response: SchemaVariantForm;
  custom: CustomSchemaForm[];
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

const emptyConstraints = (): SchemaConstraintForm => ({
  min_length: "",
  max_length: "",
  pattern: "",
  ge: "",
  le: "",
  gt: "",
  lt: "",
  min_items: "",
  max_items: "",
});

const fieldTypeOptions = [
  "String",
  "Integer",
  "Float",
  "Boolean",
  "DateTime",
  "EmailStr",
  "UUID",
  "Decimal",
  "List[String]",
  "List[Integer]",
  "List[Float]",
  "List[Boolean]",
];

const relationModeOptions = [
  { value: "embedded", label: "Embedded" },
  { value: "ids", label: "IDs" },
  { value: "omit", label: "Omit" },
];

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

const stringifyValue = (value: unknown) => {
  if (value === undefined || value === null) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
};

const parseValue = (value: string) => {
  if (!value.trim()) {
    return undefined;
  }
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
};

const parseNumber = (value: string) => {
  if (!value.trim()) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? undefined : parsed;
};

const buildSchemaFields = (fields: FieldForm[], relations: RelationForm[]) => {
  const merged = [...fields];
  const existing = new Set(fields.map((field) => field.name));
  relations
    .filter((relation) => relation.type === "belongs_to")
    .forEach((relation) => {
      const fkName =
        relation.foreign_key || `${relation.target.replace(/s$/, "")}_id`;
      if (existing.has(fkName)) {
        return;
      }
      merged.push({
        name: fkName,
        type: "String",
        nullable: relation.nullable,
        unique: false,
      });
      existing.add(fkName);
    });
  return merged;
};

const defaultRelationMode = (relation: RelationForm) => {
  if (relation.type === "has_many" || relation.type === "many_to_many") {
    return "embedded";
  }
  return "ids";
};

const buildSchemaField = (
  field: FieldForm,
  required: boolean,
  source: "model" | "custom"
): SchemaFieldForm => ({
  name: field.name,
  type: field.type,
  required,
  enabled: true,
  defaultValue: "",
  description: "",
  example: "",
  constraints: emptyConstraints(),
  source,
});

const mergeSchemaFields = (
  defaults: SchemaFieldForm[],
  overrides: any[] = [],
  requiredDefault?: boolean
) => {
  const overrideMap = new Map(
    overrides.filter((field) => field?.name).map((field) => [field.name, field])
  );
  const merged = defaults.map((field) => {
    const override = overrideMap.get(field.name);
    if (!override) {
      return field;
    }
    overrideMap.delete(field.name);
    const nextRequired =
      typeof override.required === "boolean"
        ? override.required
        : requiredDefault ?? field.required;
    return {
      ...field,
      type: override.type ?? field.type,
      required: nextRequired,
      enabled: override.enabled ?? field.enabled,
      defaultValue: stringifyValue(override.default ?? field.defaultValue),
      description: override.description ?? field.description,
      example: stringifyValue(override.example ?? field.example),
      constraints: {
        ...emptyConstraints(),
        ...(override.constraints ?? {}),
      },
    };
  });
  overrideMap.forEach((override) => {
    merged.push({
      name: override.name ?? "field",
      type: override.type ?? "String",
      required:
        typeof override.required === "boolean"
          ? override.required
          : requiredDefault ?? true,
      enabled: override.enabled ?? true,
      defaultValue: stringifyValue(override.default),
      description: override.description ?? "",
      example: stringifyValue(override.example),
      constraints: {
        ...emptyConstraints(),
        ...(override.constraints ?? {}),
      },
      source: "custom",
    });
  });
  return merged;
};

const mergeSchemaRelations = (
  relations: RelationForm[],
  overrides: any[] = []
) => {
  const overrideMap = new Map(
    overrides.filter((relation) => relation?.name).map((relation) => [
      relation.name,
      relation,
    ])
  );
  return relations.map((relation) => ({
    name: relation.name,
    mode: (overrideMap.get(relation.name)?.mode ??
      defaultRelationMode(relation)) as SchemaRelationForm["mode"],
  }));
};

const normalizeSchemas = (spec: SpecForm, rawSchemas?: any): SchemaSpecForm => {
  const baseFields = buildSchemaFields(spec.fields, spec.relations);
  const createDefaults = baseFields.map((field) =>
    buildSchemaField(field, !field.nullable, "model")
  );
  const updateDefaults = baseFields.map((field) =>
    buildSchemaField(field, false, "model")
  );
  const responseDefaults = baseFields.map((field) =>
    buildSchemaField(field, !field.nullable, "model")
  );
  return {
    create: {
      fields: mergeSchemaFields(
        createDefaults,
        rawSchemas?.create?.fields ?? [],
        undefined
      ),
      relations: rawSchemas?.create?.relations ?? [],
    },
    update: {
      fields: mergeSchemaFields(
        updateDefaults,
        rawSchemas?.update?.fields ?? [],
        false
      ),
      relations: rawSchemas?.update?.relations ?? [],
    },
    response: {
      fields: mergeSchemaFields(
        responseDefaults,
        rawSchemas?.response?.fields ?? [],
        undefined
      ),
      relations: mergeSchemaRelations(
        spec.relations,
        rawSchemas?.response?.relations ?? []
      ),
    },
    custom: (rawSchemas?.custom ?? []).map((schema: any) => ({
      name: schema.name ?? "CustomSchema",
      fields: mergeSchemaFields(
        [],
        schema.fields ?? [],
        undefined
      ).map((field) => ({ ...field, source: "custom" })),
    })),
  };
};

const serializeConstraints = (constraints: SchemaConstraintForm) => {
  const payload: Record<string, unknown> = {};
  const mapping = [
    ["min_length", parseNumber(constraints.min_length)],
    ["max_length", parseNumber(constraints.max_length)],
    ["pattern", constraints.pattern || undefined],
    ["ge", parseNumber(constraints.ge)],
    ["le", parseNumber(constraints.le)],
    ["gt", parseNumber(constraints.gt)],
    ["lt", parseNumber(constraints.lt)],
    ["min_items", parseNumber(constraints.min_items)],
    ["max_items", parseNumber(constraints.max_items)],
  ];
  mapping.forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      payload[key as string] = value;
    }
  });
  return payload;
};

const serializeFields = (fields: SchemaFieldForm[]) =>
  fields.map((field) => {
    const payload: Record<string, unknown> = {
      name: field.name,
      type: field.type,
      required: field.required,
      enabled: field.enabled,
    };
    const defaultValue = parseValue(field.defaultValue);
    if (defaultValue !== undefined) {
      payload.default = defaultValue;
    }
    if (field.description.trim()) {
      payload.description = field.description.trim();
    }
    const example = parseValue(field.example);
    if (example !== undefined) {
      payload.example = example;
    }
    const constraints = serializeConstraints(field.constraints);
    if (Object.keys(constraints).length > 0) {
      payload.constraints = constraints;
    }
    return payload;
  });

const serializeSchemas = (schemas: SchemaSpecForm) => ({
  create: {
    fields: serializeFields(schemas.create.fields),
    relations: schemas.create.relations,
  },
  update: {
    fields: serializeFields(schemas.update.fields),
    relations: schemas.update.relations,
  },
  response: {
    fields: serializeFields(schemas.response.fields),
    relations: schemas.response.relations,
  },
  custom: schemas.custom.map((schema) => ({
    name: schema.name,
    fields: serializeFields(schema.fields),
  })),
});

export default function SchemaEditor() {
  const [specItems, setSpecItems] = useState<SpecItem[]>([]);
  const [specPath, setSpecPath] = useState("");
  const [spec, setSpec] = useState<SpecForm>(emptySpec());
  const [schemas, setSchemas] = useState<SchemaSpecForm>(
    normalizeSchemas(emptySpec())
  );
  const [status, setStatus] = useState<StatusState>({
    tone: "idle",
    message: "Ready.",
  });
  const [isBusy, setIsBusy] = useState(false);
  const [activeTab, setActiveTab] = useState<
    "create" | "update" | "response" | "custom"
  >("create");
  const [showAdvanced, setShowAdvanced] = useState({
    create: false,
    update: false,
    response: false,
    custom: false,
  });

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

  useEffect(() => {
    loadSpecs();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const path = params.get("path");
    if (path) {
      selectSpec(path);
    }
  }, []);

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
      setSchemas(normalizeSchemas(normalized, data.spec?.schemas));
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
    try {
      setIsBusy(true);
      const payload = {
        ...spec,
        schemas: serializeSchemas(schemas),
      };
      await fetchJson("/specs/write", {
        method: "POST",
        body: JSON.stringify({ path: specPath, spec: payload }),
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

  const updateVariantField = (
    variant: keyof SchemaSpecForm,
    index: number,
    updates: Partial<SchemaFieldForm>
  ) => {
    if (variant === "custom") {
      return;
    }
    setSchemas((current) => ({
      ...current,
      [variant]: {
        ...current[variant],
        fields: current[variant].fields.map((field, idx) =>
          idx === index ? { ...field, ...updates } : field
        ),
      },
    }));
  };

  const toggleVariantField = (
    variant: keyof SchemaSpecForm,
    index: number,
    key: "required" | "enabled"
  ) => {
    if (variant === "custom") {
      return;
    }
    updateVariantField(variant, index, {
      [key]: !schemas[variant].fields[index][key],
    });
  };

  const addVariantField = (variant: "create" | "update" | "response") => {
    setSchemas((current) => ({
      ...current,
      [variant]: {
        ...current[variant],
        fields: [
          ...current[variant].fields,
          {
            name: "custom_field",
            type: "String",
            required: variant === "update" ? false : true,
            enabled: true,
            defaultValue: "",
            description: "",
            example: "",
            constraints: emptyConstraints(),
            source: "custom",
          },
        ],
      },
    }));
  };

  const removeVariantField = (
    variant: "create" | "update" | "response",
    index: number
  ) => {
    setSchemas((current) => ({
      ...current,
      [variant]: {
        ...current[variant],
        fields: current[variant].fields.filter((_, idx) => idx !== index),
      },
    }));
  };

  const updateRelationMode = (index: number, mode: SchemaRelationForm["mode"]) =>
    setSchemas((current) => ({
      ...current,
      response: {
        ...current.response,
        relations: current.response.relations.map((relation, idx) =>
          idx === index ? { ...relation, mode } : relation
        ),
      },
    }));

  const addCustomSchema = () =>
    setSchemas((current) => ({
      ...current,
      custom: [
        ...current.custom,
        {
          name: "CustomSchema",
          fields: [],
        },
      ],
    }));

  const updateCustomSchema = (
    index: number,
    updates: Partial<CustomSchemaForm>
  ) =>
    setSchemas((current) => ({
      ...current,
      custom: current.custom.map((schema, idx) =>
        idx === index ? { ...schema, ...updates } : schema
      ),
    }));

  const removeCustomSchema = (index: number) =>
    setSchemas((current) => ({
      ...current,
      custom: current.custom.filter((_, idx) => idx !== index),
    }));

  const addCustomField = (schemaIndex: number) =>
    setSchemas((current) => ({
      ...current,
      custom: current.custom.map((schema, idx) =>
        idx === schemaIndex
          ? {
              ...schema,
              fields: [
                ...schema.fields,
                {
                  name: "custom_field",
                  type: "String",
                  required: true,
                  enabled: true,
                  defaultValue: "",
                  description: "",
                  example: "",
                  constraints: emptyConstraints(),
                  source: "custom",
                },
              ],
            }
          : schema
      ),
    }));

  const updateCustomField = (
    schemaIndex: number,
    fieldIndex: number,
    updates: Partial<SchemaFieldForm>
  ) =>
    setSchemas((current) => ({
      ...current,
      custom: current.custom.map((schema, idx) =>
        idx === schemaIndex
          ? {
              ...schema,
              fields: schema.fields.map((field, fIdx) =>
                fIdx === fieldIndex ? { ...field, ...updates } : field
              ),
            }
          : schema
      ),
    }));

  const removeCustomField = (schemaIndex: number, fieldIndex: number) =>
    setSchemas((current) => ({
      ...current,
      custom: current.custom.map((schema, idx) =>
        idx === schemaIndex
          ? {
              ...schema,
              fields: schema.fields.filter((_, fIdx) => fIdx !== fieldIndex),
            }
          : schema
      ),
    }));

  const toggleCustomField = (
    schemaIndex: number,
    fieldIndex: number,
    key: "required" | "enabled"
  ) => {
    const field = schemas.custom[schemaIndex].fields[fieldIndex];
    updateCustomField(schemaIndex, fieldIndex, { [key]: !field[key] });
  };

  const renderFieldEditor = (
    field: SchemaFieldForm,
    onChange: (updates: Partial<SchemaFieldForm>) => void,
    onToggle: (key: "required" | "enabled") => void,
    onRemove?: () => void,
    showAdvancedFields?: boolean
  ) => (
    <div className="space-y-3 rounded-2xl border border-border/60 bg-background/70 p-4">
      <div className="grid gap-3 md:grid-cols-2">
        <FieldBlock label="Nombre">
          <Input
            value={field.name}
            readOnly={field.source === "model"}
            onChange={(event) => onChange({ name: event.target.value })}
          />
        </FieldBlock>
        <FieldBlock label="Tipo">
          <select
            value={field.type}
            onChange={(event) => onChange({ type: event.target.value })}
            className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
          >
            {fieldTypeOptions.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </FieldBlock>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <Toggle checked={field.required} onChange={() => onToggle("required")} />
          Required
        </label>
        <label className="flex items-center gap-2 text-xs text-muted-foreground">
          <Toggle checked={field.enabled} onChange={() => onToggle("enabled")} />
          Enabled
        </label>
        {onRemove ? (
          <Button size="sm" variant="outline" onClick={onRemove}>
            Remove
          </Button>
        ) : null}
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <FieldBlock label="Default" info="Valor por defecto si no se envia.">
          <Input
            placeholder="null"
            value={field.defaultValue}
            onChange={(event) => onChange({ defaultValue: event.target.value })}
          />
        </FieldBlock>
        <FieldBlock label="Descripcion" info="Se muestra en el schema y docs.">
          <Input
            placeholder="Explica el campo"
            value={field.description}
            onChange={(event) => onChange({ description: event.target.value })}
          />
        </FieldBlock>
        <FieldBlock label="Example" info="Ejemplo rapido de uso.">
          <Input
            placeholder={'"sample"'}
            value={field.example}
            onChange={(event) => onChange({ example: event.target.value })}
          />
        </FieldBlock>
      </div>
      {showAdvancedFields ? (
        <div className="grid gap-3 rounded-2xl border border-border/40 bg-muted/30 p-3 md:grid-cols-3">
          <FieldBlock label="Min length">
            <Input
              value={field.constraints.min_length}
              onChange={(event) =>
                onChange({
                  constraints: {
                    ...field.constraints,
                    min_length: event.target.value,
                  },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Max length">
            <Input
              value={field.constraints.max_length}
              onChange={(event) =>
                onChange({
                  constraints: {
                    ...field.constraints,
                    max_length: event.target.value,
                  },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Pattern">
            <Input
              value={field.constraints.pattern}
              onChange={(event) =>
                onChange({
                  constraints: {
                    ...field.constraints,
                    pattern: event.target.value,
                  },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Ge">
            <Input
              value={field.constraints.ge}
              onChange={(event) =>
                onChange({
                  constraints: { ...field.constraints, ge: event.target.value },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Le">
            <Input
              value={field.constraints.le}
              onChange={(event) =>
                onChange({
                  constraints: { ...field.constraints, le: event.target.value },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Gt">
            <Input
              value={field.constraints.gt}
              onChange={(event) =>
                onChange({
                  constraints: { ...field.constraints, gt: event.target.value },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Lt">
            <Input
              value={field.constraints.lt}
              onChange={(event) =>
                onChange({
                  constraints: { ...field.constraints, lt: event.target.value },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Min items">
            <Input
              value={field.constraints.min_items}
              onChange={(event) =>
                onChange({
                  constraints: {
                    ...field.constraints,
                    min_items: event.target.value,
                  },
                })
              }
            />
          </FieldBlock>
          <FieldBlock label="Max items">
            <Input
              value={field.constraints.max_items}
              onChange={(event) =>
                onChange({
                  constraints: {
                    ...field.constraints,
                    max_items: event.target.value,
                  },
                })
              }
            />
          </FieldBlock>
        </div>
      ) : null}
    </div>
  );

  const currentVariant =
    activeTab === "custom" ? schemas.create : schemas[activeTab];

  return (
    <main className="relative min-h-screen overflow-hidden px-6 py-10 sm:px-10">
      <div className="pointer-events-none absolute left-10 top-16 hidden h-24 w-24 rounded-full bg-accent/30 blur-2xl sm:block" />
      <div className="pointer-events-none absolute right-16 top-24 hidden h-32 w-32 rounded-full bg-primary/25 blur-3xl sm:block" />
      <div className="pointer-events-none absolute bottom-16 left-24 hidden h-28 w-28 rounded-full bg-secondary/40 blur-3xl sm:block" />

      <section className="mx-auto flex max-w-6xl flex-col gap-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <Badge variant="accent">Schema Editor</Badge>
              <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                Validation ready
              </span>
            </div>
            <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Define schemas con foco en validacion y UX.
            </h1>
            <p className="max-w-2xl text-base text-muted-foreground">
              Ajusta payloads, respuestas y validaciones avanzadas con un flujo
              guiado.
            </p>
          </div>
          <div className="flex w-full max-w-sm flex-col gap-3">
            <Button asChild variant="secondary">
              <Link href="/">Volver a endpoints</Link>
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
                    status.tone === "error" &&
                      "border-destructive/40 bg-destructive/10",
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
            <CardHeader>
              <CardTitle>Endpoints</CardTitle>
              <CardDescription>Selecciona una version para editar.</CardDescription>
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
                onClick={loadSpecs}
                disabled={isBusy}
              >
                Refresh list
              </Button>
            </CardContent>
          </Card>

          <Card className="animate-fade-up">
            <CardHeader>
              <CardTitle>Editar schemas</CardTitle>
              <CardDescription>
                Guarda cambios para regenerar los schemas del endpoint.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Section title="Contexto" info="Datos de referencia para el schema.">
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
                  <FieldBlock label="Plural">
                    <Input value={spec.plural} readOnly />
                  </FieldBlock>
                </div>
                <HelperText>
                  Cambia version o identidad desde el editor principal.
                </HelperText>
              </Section>

              <Section
                title="Variantes"
                info="Create, Update y Response se generan automaticamente."
                actions={
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      setShowAdvanced((current) => ({
                        ...current,
                        [activeTab]: !current[activeTab],
                      }))
                    }
                  >
                    {showAdvanced[activeTab]
                      ? "Ocultar validaciones"
                      : "Mostrar validaciones"}
                  </Button>
                }
              >
                <div className="flex flex-wrap gap-2">
                  {["create", "update", "response", "custom"].map((tab) => (
                    <button
                      key={tab}
                      type="button"
                      onClick={() =>
                        setActiveTab(tab as "create" | "update" | "response" | "custom")
                      }
                      className={cn(
                        "rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em]",
                        activeTab === tab
                          ? "border-primary/60 bg-primary/10 text-primary"
                          : "border-border/60 text-muted-foreground"
                      )}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </Section>

              {activeTab !== "custom" ? (
                <>
                  <Section
                    title="Campos"
                    info="Personaliza cada campo por variante."
                  >
                    <div className="space-y-3">
                      {currentVariant.fields.map((field, index) => (
                        <div key={`${field.name}-${index}`}>
                          {renderFieldEditor(
                            field,
                            (updates) =>
                              updateVariantField(activeTab, index, updates),
                            (key) => toggleVariantField(activeTab, index, key),
                            field.source === "custom"
                              ? () => removeVariantField(activeTab, index)
                              : undefined,
                            showAdvanced[activeTab]
                          )}
                        </div>
                      ))}
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      className="mt-4"
                      onClick={() => addVariantField(activeTab)}
                    >
                      Add custom field
                    </Button>
                  </Section>

                  {activeTab === "response" ? (
                    <Section
                      title="Relaciones"
                      info="Define si la respuesta embebe o reduce a IDs."
                    >
                      <div className="space-y-3">
                        {schemas.response.relations.map((relation, index) => (
                          <div
                            key={relation.name}
                            className="flex flex-col gap-3 rounded-2xl border border-border/60 bg-background/70 p-4 md:flex-row md:items-center md:justify-between"
                          >
                            <div>
                              <div className="text-sm font-semibold text-foreground">
                                {relation.name}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {spec.relations.find(
                                  (item) => item.name === relation.name
                                )?.type ?? "relation"}
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <select
                                value={relation.mode}
                                onChange={(event) =>
                                  updateRelationMode(
                                    index,
                                    event.target.value as SchemaRelationForm["mode"]
                                  )
                                }
                                className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
                              >
                                {relationModeOptions.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                              <InfoTip text="IDs mantiene solo el FK, Embedded agrega el objeto relacionado." />
                            </div>
                          </div>
                        ))}
                      </div>
                    </Section>
                  ) : null}
                </>
              ) : (
                <Section
                  title="Custom schemas"
                  info="Define esquemas adicionales para casos especificos."
                >
                  <div className="space-y-4">
                    {schemas.custom.map((schema, index) => (
                      <div
                        key={`${schema.name}-${index}`}
                        className="space-y-3 rounded-3xl border border-border/60 bg-background/70 p-4"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <FieldBlock label="Nombre">
                            <Input
                              value={schema.name}
                              onChange={(event) =>
                                updateCustomSchema(index, {
                                  name: event.target.value,
                                })
                              }
                            />
                          </FieldBlock>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => removeCustomSchema(index)}
                          >
                            Remove schema
                          </Button>
                        </div>
                        <div className="space-y-3">
                          {schema.fields.map((field, fieldIndex) => (
                            <div key={`${field.name}-${fieldIndex}`}>
                              {renderFieldEditor(
                                field,
                                (updates) =>
                                  updateCustomField(index, fieldIndex, updates),
                                (key) =>
                                  toggleCustomField(index, fieldIndex, key),
                                () => removeCustomField(index, fieldIndex),
                                showAdvanced.custom
                              )}
                            </div>
                          ))}
                        </div>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => addCustomField(index)}
                        >
                          Add field
                        </Button>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center gap-3">
                    <Button variant="secondary" size="sm" onClick={addCustomSchema}>
                      Add custom schema
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setShowAdvanced((current) => ({
                          ...current,
                          custom: !current.custom,
                        }))
                      }
                    >
                      {showAdvanced.custom
                        ? "Ocultar validaciones"
                        : "Mostrar validaciones"}
                    </Button>
                  </div>
                </Section>
              )}

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
    </main>
  );
}
