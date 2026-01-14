"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
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
import { FieldBlock, HelperText, Section, ToggleRow } from "@/components/scaffold-ui";
import { fetchJson } from "@/lib/scaffold-api";
import { cn } from "@/lib/utils";
import { useScaffoldStatus } from "@/components/scaffold-status";

type ExternalConnection = {
  name: string;
  url: string;
  permissions: string[];
  backend?: string;
  source?: string;
};

const engineOptions = [
  {
    value: "sqlite",
    label: "SQLite",
    example: "sqlite:///./app/external.db",
  },
  {
    value: "postgresql",
    label: "PostgreSQL",
    example: "postgresql+psycopg2://user:pass@host/dbname",
  },
  {
    value: "mariadb",
    label: "MariaDB",
    example: "mysql+pymysql://user:pass@host/dbname",
  },
];

const permissionOptions = ["create", "read", "update", "delete"] as const;
type Permission = (typeof permissionOptions)[number];
type ToastTone = "success" | "error";
type ToastState = {
  tone: ToastTone;
  title: string;
  message: string;
};

const emptyPermissions = () =>
  permissionOptions.reduce(
    (acc, perm) => ({ ...acc, [perm]: true }),
    {} as Record<Permission, boolean>
  );

export default function ExternalDatabasesPage() {
  const { setStatus } = useScaffoldStatus();
  const [connections, setConnections] = useState<ExternalConnection[]>([]);
  const [isBusy, setIsBusy] = useState(false);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [formName, setFormName] = useState("");
  const [engine, setEngine] = useState(engineOptions[0].value);
  const [sqlitePath, setSqlitePath] = useState("");
  const [host, setHost] = useState("");
  const [port, setPort] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [database, setDatabase] = useState("");
  const [manualConnectionUrl, setManualConnectionUrl] = useState("");
  const [isManualConnection, setIsManualConnection] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [permissions, setPermissions] = useState<Record<Permission, boolean>>(
    emptyPermissions()
  );

  useEffect(() => {
    loadConnections();
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimer.current) {
        clearTimeout(toastTimer.current);
      }
    };
  }, []);

  const loadConnections = async () => {
    try {
      const data = await fetchJson("/external-dbs");
      setConnections(data.connections ?? []);
      setStatus({ tone: "success", message: "External DBs loaded." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

  const resetForm = () => {
    setSelectedName(null);
    setFormName("");
    setEngine(engineOptions[0].value);
    setSqlitePath("");
    setHost("");
    setPort("");
    setUsername("");
    setPassword("");
    setDatabase("");
    setManualConnectionUrl("");
    setIsManualConnection(false);
    setPermissions(emptyPermissions());
  };

  const selectConnection = (connection: ExternalConnection) => {
    const parsed = parseConnectionUrl(connection.url);
    setSelectedName(connection.name);
    setFormName(connection.name);
    setEngine(parsed.engine);
    setSqlitePath(parsed.sqlitePath);
    setHost(parsed.host);
    setPort(parsed.port);
    setUsername(parsed.username);
    setPassword(parsed.password);
    setDatabase(parsed.database);
    setManualConnectionUrl(connection.url);
    setIsManualConnection(false);
    const nextPermissions = emptyPermissions();
    permissionOptions.forEach((perm) => {
      nextPermissions[perm] = connection.permissions.includes(perm);
    });
    setPermissions(nextPermissions);
  };

  const selectedPermissions = useMemo(
    () => permissionOptions.filter((perm) => permissions[perm]),
    [permissions]
  );

  const engineExample = useMemo(() => {
    return engineOptions.find((option) => option.value === engine)?.example ?? "";
  }, [engine]);

  const engineHelper = useMemo(() => {
    if (!engineExample) {
      return "";
    }
    if (engine === "mariadb") {
      return `Ejemplo: ${engineExample} (requiere pymysql)`;
    }
    if (engine === "postgresql") {
      return `Ejemplo: ${engineExample} (requiere psycopg2)`;
    }
    return `Ejemplo: ${engineExample}`;
  }, [engine, engineExample]);

  const generatedConnectionUrl = useMemo(
    () =>
      buildConnectionUrl({
        engine,
        sqlitePath,
        host,
        port,
        username,
        password,
        database,
      }),
    [database, engine, host, password, port, sqlitePath, username]
  );
  const activeConnectionUrl = isManualConnection
    ? manualConnectionUrl.trim()
    : generatedConnectionUrl;
  const displayConnectionUrl = maskConnectionUrl(activeConnectionUrl);

  const saveConnection = async () => {
    if (!formName.trim()) {
      setStatus({ tone: "error", message: "Name is required." });
      return;
    }
    if (!activeConnectionUrl) {
      setStatus({ tone: "error", message: "Connection data is required." });
      return;
    }
    if (selectedPermissions.length === 0) {
      setStatus({
        tone: "error",
        message: "Select at least one permission.",
      });
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson("/external-dbs", {
        method: "POST",
        body: JSON.stringify({
          name: formName.trim(),
          url: activeConnectionUrl,
          permissions: selectedPermissions,
        }),
      });
      await loadConnections();
      setStatus({ tone: "success", message: "External DB saved." });
      showToast({
        tone: "success",
        title: "Conexion guardada",
        message: "La conexion se guardo correctamente.",
      });
      setSelectedName(formName.trim());
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
      showToast(toastFromError(String(error), "No se pudo guardar la conexion."));
    } finally {
      setIsBusy(false);
    }
  };

  const testConnection = async () => {
    if (!activeConnectionUrl) {
      setStatus({ tone: "error", message: "Connection data is required." });
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson("/external-dbs/test", {
        method: "POST",
        body: JSON.stringify({ url: activeConnectionUrl }),
      });
      setStatus({ tone: "success", message: "Connection OK." });
      showToast({
        tone: "success",
        title: "Conexion OK",
        message: "La conexion respondio correctamente.",
      });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
      showToast(toastFromError(String(error), "No se pudo validar la conexion."));
    } finally {
      setIsBusy(false);
    }
  };

  const deleteConnection = async (name: string) => {
    const ok = window.confirm(`Remove external connection "${name}"?`);
    if (!ok) {
      return;
    }
    try {
      setIsBusy(true);
      await fetchJson("/external-dbs/delete", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      await loadConnections();
      if (selectedName === name) {
        resetForm();
      }
      setStatus({ tone: "success", message: "External DB removed." });
      showToast({
        tone: "success",
        title: "Conexion eliminada",
        message: "La conexion se elimino correctamente.",
      });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
      showToast(toastFromError(String(error), "No se pudo eliminar la conexion."));
    } finally {
      setIsBusy(false);
    }
  };

  const toggleConnectionEditor = () => {
    setIsManualConnection((current) => {
      const next = !current;
      if (next) {
        setManualConnectionUrl((value) => value || generatedConnectionUrl);
      }
      return next;
    });
  };

  const handleManualConnectionChange = (value: string) => {
    setManualConnectionUrl(value);
    const parsed = parseConnectionUrl(value);
    setEngine(parsed.engine);
    setSqlitePath(parsed.sqlitePath);
    setHost(parsed.host);
    setPort(parsed.port);
    setUsername(parsed.username);
    setPassword(parsed.password);
    setDatabase(parsed.database);
  };

  const showToast = (next: ToastState) => {
    setToast(next);
    if (toastTimer.current) {
      clearTimeout(toastTimer.current);
    }
    toastTimer.current = setTimeout(() => {
      setToast(null);
    }, 6000);
  };

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-6">
      {toast ? (
        <div
          className={cn(
            "fixed bottom-6 right-6 z-50 max-w-sm rounded-2xl border px-4 py-3 text-sm shadow-lg",
            toast.tone === "success"
              ? "border-primary/40 bg-primary/10 text-foreground"
              : "border-destructive/40 bg-destructive/10 text-foreground"
          )}
          role="status"
          aria-live="polite"
        >
          <div className="text-sm font-semibold">{toast.title}</div>
          <div className="mt-1 text-xs text-muted-foreground">{toast.message}</div>
        </div>
      ) : null}
      <div className="flex items-center justify-between">
        <Button asChild variant="ghost" size="sm" className="gap-2">
          <Link href="/endpoints">
            <ArrowLeft className="h-4 w-4" />
            Volver a endpoints
          </Link>
        </Button>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          Bases externas
        </h1>
        <p className="text-sm text-muted-foreground">
          Registra conexiones externas y controla permisos por conexion.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <Card className="animate-fade-up">
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle>Conexiones</CardTitle>
              <CardDescription>
                Selecciona una conexion para editarla o eliminarla.
              </CardDescription>
            </div>
            <Button variant="secondary" size="sm" onClick={resetForm}>
              Nueva conexion
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {connections.length === 0 && (
              <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                No hay conexiones externas configuradas.
              </div>
            )}
            {connections.map((connection, index) => {
              const isSelected = connection.name === selectedName;
              const permissionsLabel =
                connection.permissions.length === permissionOptions.length
                  ? "all"
                  : connection.permissions.join(", ");
              return (
                <div
                  key={`${connection.name}-${index}`}
                  className={`rounded-3xl border px-4 py-3 text-sm ${
                    isSelected
                      ? "border-primary/60 bg-primary/10"
                      : "border-border/60 bg-background/70"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-base font-semibold text-foreground">
                        {connection.name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {connection.backend ?? "unknown"} - {permissionsLabel}
                      </div>
                      {connection.source === "legacy" && (
                        <div className="mt-1 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                          Legacy
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => selectConnection(connection)}
                      >
                        Editar
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => deleteConnection(connection.name)}
                        disabled={isBusy}
                      >
                        Eliminar
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    {maskConnectionUrl(connection.url)}
                  </div>
                </div>
              );
            })}
            <Button variant="secondary" size="sm" onClick={loadConnections}>
              Refresh list
            </Button>
          </CardContent>
        </Card>

        <Card className="animate-fade-up">
          <CardHeader>
            <CardTitle>
              {selectedName ? "Editar conexion" : "Crear conexion"}
            </CardTitle>
            <CardDescription>
              Guarda la conexion en .env para que la API la detecte.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Section title="Identidad">
              <div className="grid gap-4 md:grid-cols-2">
                <FieldBlock label="Nombre">
                  <Input
                    placeholder="reporting"
                    value={formName}
                    onChange={(event) => setFormName(event.target.value)}
                  />
                  <HelperText>
                    Usa letras, numeros o guiones bajos.
                  </HelperText>
                </FieldBlock>
                <FieldBlock label="Motor">
                  <select
                    value={engine}
                    onChange={(event) => setEngine(event.target.value)}
                    className="h-10 rounded-2xl border border-input bg-background/70 px-3 text-sm"
                  >
                    {engineOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <HelperText>{engineHelper}</HelperText>
                </FieldBlock>
                <FieldBlock label="Connection string">
                  <div className="flex flex-wrap items-center gap-2">
                    <Input
                      value={isManualConnection ? manualConnectionUrl : displayConnectionUrl}
                      readOnly={!isManualConnection}
                      onChange={(event) => handleManualConnectionChange(event.target.value)}
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={toggleConnectionEditor}
                    >
                      {isManualConnection ? "Usar generado" : "Editar"}
                    </Button>
                  </div>
                  <HelperText>
                    {isManualConnection
                      ? "Al editar se mostrara el password y se completaran los campos."
                      : "Se genera automaticamente con los campos."}
                  </HelperText>
                </FieldBlock>
              </div>
            </Section>

            {engine === "sqlite" ? (
              <Section
                title="SQLite"
                info="Define la ruta del archivo SQLite (relativa al contenedor)."
              >
                <FieldBlock label="Ruta del archivo">
                  <Input
                    placeholder="./app/external.db"
                    value={sqlitePath}
                    onChange={(event) => setSqlitePath(event.target.value)}
                  />
                  <HelperText>
                    Usa rutas relativas para que funcione con Docker.
                  </HelperText>
                </FieldBlock>
              </Section>
            ) : (
              <Section title="Servidor" info="Datos de host y credenciales.">
                <div className="grid gap-4 md:grid-cols-2">
                  <FieldBlock label="Host">
                    <Input
                      placeholder="db.company.internal"
                      value={host}
                      onChange={(event) => setHost(event.target.value)}
                    />
                  </FieldBlock>
                  <FieldBlock label="Port">
                    <Input
                      placeholder="5432"
                      value={port}
                      onChange={(event) => setPort(event.target.value)}
                    />
                  </FieldBlock>
                  <FieldBlock label="User">
                    <Input
                      placeholder="db_user"
                      value={username}
                      onChange={(event) => setUsername(event.target.value)}
                    />
                  </FieldBlock>
                  <FieldBlock label="Password">
                    <Input
                      type="password"
                      placeholder="secret"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                    />
                  </FieldBlock>
                  <FieldBlock label="Database (optional)">
                    <Input
                      placeholder="inventory"
                      value={database}
                      onChange={(event) => setDatabase(event.target.value)}
                    />
                  </FieldBlock>
                </div>
              </Section>
            )}

            <Section
              title="Permisos"
              info="Define que operaciones permite esta conexion."
            >
              <div className="grid gap-3 md:grid-cols-2">
                {permissionOptions.map((perm) => (
                  <ToggleRow
                    key={perm}
                    label={perm}
                    checked={permissions[perm]}
                    onChange={(value) =>
                      setPermissions((current) => ({ ...current, [perm]: value }))
                    }
                  />
                ))}
              </div>
            </Section>

            <Section title="Acciones principales">
              <div className="flex flex-wrap gap-3">
                <Button onClick={saveConnection} disabled={isBusy}>
                  {selectedName ? "Guardar cambios" : "Crear conexion"}
                </Button>
                <Button variant="secondary" onClick={resetForm} disabled={isBusy}>
                  Limpiar
                </Button>
                <Button variant="outline" onClick={testConnection} disabled={isBusy}>
                  Test connection
                </Button>
              </div>
            </Section>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

type ParsedConnection = {
  engine: string;
  sqlitePath: string;
  host: string;
  port: string;
  username: string;
  password: string;
  database: string;
};

const emptyParsedConnection = (): ParsedConnection => ({
  engine: engineOptions[0].value,
  sqlitePath: "",
  host: "",
  port: "",
  username: "",
  password: "",
  database: "",
});

function buildConnectionUrl(values: ParsedConnection): string {
  const cleanedEngine = values.engine;
  if (cleanedEngine === "sqlite") {
    const rawPath = values.sqlitePath.trim();
    if (!rawPath) {
      return "";
    }
    if (rawPath.startsWith("sqlite:")) {
      return rawPath;
    }
    if (rawPath.startsWith("/")) {
      return `sqlite:////${rawPath.slice(1)}`;
    }
    const normalized = rawPath.startsWith("./") || rawPath.startsWith("../")
      ? rawPath
      : `./${rawPath}`;
    return `sqlite:///${normalized}`;
  }

  const scheme =
    cleanedEngine === "postgresql" ? "postgresql+psycopg2" : "mysql+pymysql";
  const host = values.host.trim();
  if (!host) {
    return "";
  }
  const user = values.username.trim();
  const password = values.password;
  const auth = user
    ? `${encodeURIComponent(user)}${password ? `:${encodeURIComponent(password)}` : ""}@`
    : "";
  const port = values.port.trim();
  const hostPart = port ? `${host}:${port}` : host;
  const db = values.database.trim();
  const dbPart = db ? `/${db}` : "";
  return `${scheme}://${auth}${hostPart}${dbPart}`;
}

function parseConnectionUrl(url: string): ParsedConnection {
  const parsed = emptyParsedConnection();
  const trimmed = (url ?? "").trim();
  if (!trimmed) {
    return parsed;
  }
  if (trimmed.startsWith("sqlite:")) {
    parsed.engine = "sqlite";
    if (trimmed.startsWith("sqlite:////")) {
      parsed.sqlitePath = `/${trimmed.slice("sqlite:////".length)}`;
    } else if (trimmed.startsWith("sqlite:///")) {
      parsed.sqlitePath = trimmed.slice("sqlite:///".length);
    } else {
      parsed.sqlitePath = trimmed.replace(/^sqlite:\/*/, "");
    }
    return parsed;
  }
  try {
    const parsedUrl = new URL(trimmed);
    const scheme = parsedUrl.protocol.replace(":", "");
    if (scheme.startsWith("postgresql")) {
      parsed.engine = "postgresql";
    } else if (scheme.startsWith("mariadb") || scheme.startsWith("mysql")) {
      parsed.engine = "mariadb";
    }
    parsed.host = parsedUrl.hostname;
    parsed.port = parsedUrl.port;
    parsed.username = decodeURIComponent(parsedUrl.username);
    parsed.password = decodeURIComponent(parsedUrl.password);
    parsed.database = parsedUrl.pathname.replace("/", "");
  } catch {
    return parsed;
  }
  return parsed;
}

function maskConnectionUrl(url: string): string {
  const trimmed = (url ?? "").trim();
  if (!trimmed) {
    return "";
  }
  if (trimmed.startsWith("sqlite:")) {
    return trimmed;
  }
  try {
    const parsed = new URL(trimmed);
    if (!parsed.password) {
      return trimmed;
    }
    const masked = new URL(trimmed);
    masked.password = "******";
    return masked.toString();
  } catch {
    return trimmed.replace(
      /:\/\/([^:@/]+):([^@/]+)@/g,
      "://$1:******@"
    );
  }
}

function toastFromError(message: string, fallback: string): ToastState {
  const cleaned = message.replace(/^Error:\s*/i, "").trim();
  const missingDriver = cleaned.match(/No module named ['"](.+?)['"]/i);
  if (missingDriver) {
    return {
      tone: "error",
      title: "Driver faltante",
      message: `Instala ${missingDriver[1]} en el backend.`,
    };
  }
  if (cleaned.toLowerCase().includes("operationalerror")) {
    return {
      tone: "error",
      title: "Conexion rechazada",
      message: cleaned,
    };
  }
  return {
    tone: "error",
    title: "Error de conexion",
    message: cleaned || fallback,
  };
}
