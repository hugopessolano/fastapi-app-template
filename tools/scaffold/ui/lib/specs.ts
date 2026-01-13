export type SpecSummary = {
  path: string;
  name: string;
};

export type SpecItem = {
  path: string;
  name: string;
  version: string;
  plural: string;
  tags: string[];
};

export type FieldForm = {
  name: string;
  type: string;
  nullable: boolean;
  unique: boolean;
};

export type RelationForm = {
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

export type SpecForm = {
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

export type StatusTone = "idle" | "success" | "error";

export type StatusState = {
  tone: StatusTone;
  message: string;
};

export const emptySpec = (): SpecForm => ({
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

export const normalizeSpec = (raw: Partial<SpecForm>): SpecForm => {
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

export function nextVersion(versions: string[]) {
  const numbers = versions
    .map((version) => Number.parseInt(version.replace(/\D/g, ""), 10))
    .filter((value) => !Number.isNaN(value));
  const next = numbers.length > 0 ? Math.max(...numbers) + 1 : 1;
  return `v${next}`;
}

export function buildVersionPath(path: string, version: string) {
  const parts = path.split("/");
  const filename = parts.pop() ?? "endpoint.json";
  const base = filename.replace(/_v\d+\.json$/i, "").replace(/\.json$/i, "");
  return [...parts, `${base}_${version}.json`].join("/");
}
