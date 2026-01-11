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

type SettingValue = string | number | boolean;

type SettingField = {
  key: string;
  label: string;
  info: string;
  type: "string" | "number" | "boolean" | "select";
  group: string;
  options?: string[];
  placeholder?: string;
};

type StatusState = {
  tone: "idle" | "success" | "error";
  message: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_SCAFFOLD_API_URL ?? "http://127.0.0.1:8001";

const settingsDefaults: Record<string, SettingValue> = {
  APP_NAME: "FastAPI Template",
  ENVIRONMENT: "development",
  AUTH_MODE: "built_in",
  TENANTS_ENABLED: true,
  AUTO_BUILD_PERMISSIONS: true,
  ENABLE_SEED_DATA: true,
  SEED_CHECK_EXISTING_USERS: true,
  RATE_LIMIT_DEFAULT_REQUESTS: 60,
  RATE_LIMIT_DEFAULT_WINDOW_SECONDS: 60,
  RETRY_MAX_ATTEMPTS: 3,
  RETRY_BASE_DELAY_SECONDS: 0.2,
  RETRY_MAX_DELAY_SECONDS: 2.0,
  RETRY_JITTER_SECONDS: 0.1,
  CACHE_ENABLED: false,
  CACHE_DEFAULT_TTL_SECONDS: 60,
  LOGGING_STDOUT_LEVEL: "INFO",
  LOGGING_DB_LEVEL: "INFO",
  DATABASE_URL: "sqlite:///./app/app.db",
  EXTERNAL_DB_URL: "",
};

const settingsFields: SettingField[] = [
  {
    key: "APP_NAME",
    label: "App name",
    info: "Nombre visible en OpenAPI y logs.",
    type: "string",
    group: "API",
  },
  {
    key: "ENVIRONMENT",
    label: "Environment",
    info: "Entorno actual (development, staging, production).",
    type: "string",
    group: "API",
  },
  {
    key: "AUTH_MODE",
    label: "Auth mode",
    info: "built_in, disabled o custom.",
    type: "select",
    group: "Auth y tenants",
    options: ["built_in", "disabled", "custom"],
  },
  {
    key: "TENANTS_ENABLED",
    label: "Tenants enabled",
    info: "Habilita aislamiento por tenants.",
    type: "boolean",
    group: "Auth y tenants",
  },
  {
    key: "AUTO_BUILD_PERMISSIONS",
    label: "Auto build permissions",
    info: "Genera permisos al iniciar.",
    type: "boolean",
    group: "Auth y tenants",
  },
  {
    key: "ENABLE_SEED_DATA",
    label: "Enable seed data",
    info: "Crea datos iniciales al iniciar.",
    type: "boolean",
    group: "Auth y tenants",
  },
  {
    key: "SEED_CHECK_EXISTING_USERS",
    label: "Seed check existing users",
    info: "Evita recrear admin si ya hay usuarios.",
    type: "boolean",
    group: "Auth y tenants",
  },
  {
    key: "RATE_LIMIT_DEFAULT_REQUESTS",
    label: "Rate limit requests",
    info: "Maximo de requests por ventana.",
    type: "number",
    group: "Rate limit",
  },
  {
    key: "RATE_LIMIT_DEFAULT_WINDOW_SECONDS",
    label: "Rate limit window (sec)",
    info: "Ventana en segundos para rate limit.",
    type: "number",
    group: "Rate limit",
  },
  {
    key: "RETRY_MAX_ATTEMPTS",
    label: "Retry max attempts",
    info: "Intentos maximos para reintentos.",
    type: "number",
    group: "Retries",
  },
  {
    key: "RETRY_BASE_DELAY_SECONDS",
    label: "Retry base delay (sec)",
    info: "Delay inicial para backoff.",
    type: "number",
    group: "Retries",
  },
  {
    key: "RETRY_MAX_DELAY_SECONDS",
    label: "Retry max delay (sec)",
    info: "Delay maximo para backoff.",
    type: "number",
    group: "Retries",
  },
  {
    key: "RETRY_JITTER_SECONDS",
    label: "Retry jitter (sec)",
    info: "Jitter agregado al backoff.",
    type: "number",
    group: "Retries",
  },
  {
    key: "CACHE_ENABLED",
    label: "Cache enabled",
    info: "Activa cache por defecto.",
    type: "boolean",
    group: "Cache",
  },
  {
    key: "CACHE_DEFAULT_TTL_SECONDS",
    label: "Cache TTL (sec)",
    info: "Tiempo de vida por defecto.",
    type: "number",
    group: "Cache",
  },
  {
    key: "LOGGING_STDOUT_LEVEL",
    label: "Logging stdout level",
    info: "Nivel de logs en consola.",
    type: "select",
    group: "Logging",
    options: ["DEBUG", "INFO", "WARNING", "ERROR"],
  },
  {
    key: "LOGGING_DB_LEVEL",
    label: "Logging DB level",
    info: "Nivel de logs en base.",
    type: "select",
    group: "Logging",
    options: ["DEBUG", "INFO", "WARNING", "ERROR"],
  },
  {
    key: "DATABASE_URL",
    label: "Database URL",
    info: "Conexion principal de la API.",
    type: "string",
    group: "Database",
  },
  {
    key: "EXTERNAL_DB_URL",
    label: "External DB URL",
    info: "Conexion externa opcional.",
    type: "string",
    group: "Database",
  },
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

const normalizeSettings = (raw: Record<string, string>): Record<string, SettingValue> => {
  const next = { ...settingsDefaults };
  settingsFields.forEach((field) => {
    const rawValue = raw[field.key];
    if (rawValue === undefined) {
      return;
    }
    if (field.type === "boolean") {
      const normalized = rawValue.toLowerCase();
      next[field.key] = ["true", "1", "yes", "on"].includes(normalized);
      return;
    }
    if (field.type === "number") {
      const parsed = Number(rawValue);
      next[field.key] = Number.isNaN(parsed)
        ? (settingsDefaults[field.key] as number)
        : parsed;
      return;
    }
    next[field.key] = rawValue;
  });
  return next;
};

const serializeSettings = (settings: Record<string, SettingValue>) => {
  const payload: Record<string, string> = {};
  settingsFields.forEach((field) => {
    const value = settings[field.key];
    if (field.type === "boolean") {
      payload[field.key] = value ? "true" : "false";
      return;
    }
    payload[field.key] = String(value ?? "");
  });
  return payload;
};

export default function SettingsPage() {
  const [generalSettings, setGeneralSettings] = useState<Record<string, SettingValue>>(
    settingsDefaults
  );
  const [status, setStatus] = useState<StatusState>({
    tone: "idle",
    message: "Ready.",
  });
  const [isBusy, setIsBusy] = useState(false);

  const settingsGroups = useMemo(() => {
    const groups = new Map<string, SettingField[]>();
    settingsFields.forEach((field) => {
      if (!groups.has(field.group)) {
        groups.set(field.group, []);
      }
      groups.get(field.group)?.push(field);
    });
    return Array.from(groups.entries()).map(([group, fields]) => ({
      group,
      fields,
    }));
  }, []);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await fetchJson("/settings");
      const normalized = normalizeSettings(data.settings ?? {});
      setGeneralSettings(normalized);
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

  const saveSettings = async () => {
    try {
      setIsBusy(true);
      const payload = serializeSettings(generalSettings);
      await fetchJson("/settings", {
        method: "POST",
        body: JSON.stringify({ settings: payload }),
      });
      setStatus({ tone: "success", message: "Settings saved." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const updateSetting = (key: string, value: SettingValue) =>
    setGeneralSettings((current) => ({ ...current, [key]: value }));

  const renderSettingField = (field: SettingField) => {
    const value = generalSettings[field.key] ?? settingsDefaults[field.key];
    if (field.type === "boolean") {
      return (
        <FieldBlock key={field.key} label={field.label} info={field.info}>
          <div className="flex items-center justify-between rounded-2xl border border-border/60 bg-background/70 px-3 py-2 text-sm">
            <span className="text-muted-foreground">
              {value ? "Enabled" : "Disabled"}
            </span>
            <Toggle
              checked={Boolean(value)}
              onChange={(checked) => updateSetting(field.key, checked)}
            />
          </div>
        </FieldBlock>
      );
    }

    if (field.type === "select") {
      return (
        <FieldBlock key={field.key} label={field.label} info={field.info}>
          <select
            value={String(value ?? "")}
            onChange={(event) => updateSetting(field.key, event.target.value)}
            className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
          >
            {field.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </FieldBlock>
      );
    }

    if (field.type === "number") {
      return (
        <FieldBlock key={field.key} label={field.label} info={field.info}>
          <Input
            type="number"
            value={String(value ?? "")}
            onChange={(event) => {
              const parsed = Number(event.target.value);
              updateSetting(
                field.key,
                Number.isNaN(parsed)
                  ? (settingsDefaults[field.key] as number)
                  : parsed
              );
            }}
          />
        </FieldBlock>
      );
    }

    return (
      <FieldBlock key={field.key} label={field.label} info={field.info}>
        <Input
          placeholder={field.placeholder}
          value={String(value ?? "")}
          onChange={(event) => updateSetting(field.key, event.target.value)}
        />
      </FieldBlock>
    );
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
              <Badge variant="accent">Configuracion general</Badge>
              <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                Defaults
              </span>
            </div>
            <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">
              Configura los defaults globales de la API.
            </h1>
            <p className="max-w-2xl text-base text-muted-foreground">
              Estos valores afectan el comportamiento global del template. Ajustalos
              antes de generar endpoints mas finos.
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

        <Card className="animate-fade-up">
          <CardHeader>
            <CardTitle>Defaults globales</CardTitle>
            <CardDescription>
              Cada grupo explica el parametro con un tooltip.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {settingsGroups.map((group) => (
              <div key={group.group} className="space-y-3">
                <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                  {group.group}
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  {group.fields.map((field) => renderSettingField(field))}
                </div>
              </div>
            ))}
            <div className="mt-5 flex flex-wrap gap-3">
              <Button onClick={saveSettings} disabled={isBusy}>
                Guardar configuracion
              </Button>
              <Button
                variant="secondary"
                onClick={loadSettings}
                disabled={isBusy}
              >
                Refresh settings
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

function FieldBlock({
  label,
  info,
  children,
}: {
  label: string;
  info?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
        <label>{label}</label>
        {info ? <InfoTip text={info} /> : null}
      </div>
      {children}
    </div>
  );
}

function InfoTip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex">
      <span className="flex h-5 w-5 items-center justify-center rounded-full border border-border/60 text-[10px] font-semibold text-muted-foreground">
        i
      </span>
      <span className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 w-56 -translate-x-1/2 rounded-2xl border border-border/70 bg-background/95 px-3 py-2 text-xs normal-case text-muted-foreground opacity-0 shadow-lg transition group-hover:opacity-100">
        {text}
      </span>
    </span>
  );
}
