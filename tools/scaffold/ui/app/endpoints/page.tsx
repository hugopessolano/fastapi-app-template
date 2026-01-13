"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchJson } from "@/lib/scaffold-api";
import { buildVersionPath, nextVersion, SpecItem, SpecSummary } from "@/lib/specs";
import { useScaffoldStatus } from "@/components/scaffold-status";

type SpecGroup = {
  name: string;
  items: SpecItem[];
};

export default function EndpointsPage() {
  const router = useRouter();
  const { setStatus } = useScaffoldStatus();
  const [specItems, setSpecItems] = useState<SpecItem[]>([]);
  const [selectedVersions, setSelectedVersions] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    loadSpecs();
  }, []);

  const groupedSpecs = useMemo<SpecGroup[]>(() => {
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

  const visibleGroups = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) {
      return groupedSpecs;
    }
    return groupedSpecs.filter((group) => {
      const matchName = group.name.toLowerCase().includes(query);
      const matchTags = group.items.some((item) =>
        item.tags.join(",").toLowerCase().includes(query)
      );
      return matchName || matchTags;
    });
  }, [filter, groupedSpecs]);

  useEffect(() => {
    if (groupedSpecs.length === 0) {
      return;
    }
    setSelectedVersions((current) => {
      const next = { ...current };
      groupedSpecs.forEach((group) => {
        const existing = next[group.name];
        const valid = group.items.some((item) => item.path === existing);
        if (!valid) {
          next[group.name] = group.items[group.items.length - 1]?.path ?? "";
        }
      });
      return next;
    });
  }, [groupedSpecs]);

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
      setStatus({ tone: "success", message: "Spec list loaded." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  };

  const navigateToEditor = (path: string) => {
    router.push(`/endpoints/editor?path=${encodeURIComponent(path)}`);
  };

  const startNewEndpoint = () => {
    router.push("/endpoints/editor");
  };

  const createNewVersion = async (group: SpecGroup, basePath: string) => {
    try {
      setIsBusy(true);
      await fetchJson(`/specs/read?path=${encodeURIComponent(basePath)}`);
      const versions = group.items.map((item) => item.version);
      const newVersion = nextVersion(versions);
      const newPath = buildVersionPath(basePath, newVersion);
      router.push(
        `/endpoints/editor?cloneFrom=${encodeURIComponent(
          basePath
        )}&newPath=${encodeURIComponent(newPath)}&newVersion=${encodeURIComponent(
          newVersion
        )}`
      );
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
      await loadSpecs();
      setStatus({ tone: "success", message: "Version deleted." });
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const updateSelectedVersion = (
    group: SpecGroup,
    selectedPath: string
  ) => {
    if (selectedPath === "__new__") {
      createNewVersion(group, group.items[group.items.length - 1].path);
      return;
    }
    setSelectedVersions((current) => ({
      ...current,
      [group.name]: selectedPath,
    }));
  };

  const selectedItemForGroup = (group: SpecGroup) => {
    const selectedPath =
      selectedVersions[group.name] ?? group.items[group.items.length - 1]?.path;
    return (
      group.items.find((item) => item.path === selectedPath) ??
      group.items[group.items.length - 1]
    );
  };

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Endpoints
          </h1>
          <p className="text-sm text-muted-foreground">
            Administra endpoints y versiones desde una vista compacta.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <Input
            placeholder="Buscar endpoints o tags"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
          />
          <Button onClick={startNewEndpoint}>Nuevo endpoint</Button>
        </div>
      </div>

      <Card className="animate-fade-up">
        <CardHeader>
          <CardTitle>Listado</CardTitle>
          <CardDescription>
            Selecciona una version o crea una nueva desde el selector.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {visibleGroups.length === 0 && (
            <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
              No hay endpoints creados todavia.
            </div>
          )}
          {visibleGroups.map((group, index) => {
            const selectedItem = selectedItemForGroup(group);
            return (
              <div
                key={group.name}
                style={{ animationDelay: `${index * 60}ms` }}
                className="animate-fade-up rounded-3xl border border-border/60 bg-background/60 p-4"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div className="space-y-1">
                    <div className="text-base font-semibold text-foreground">
                      {group.name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      /{selectedItem.version}/{selectedItem.plural} -{" "}
                      {group.items.length} version(es)
                    </div>
                    {selectedItem.tags.length > 0 && (
                      <div className="text-xs text-muted-foreground">
                        Tags: {selectedItem.tags.join(", ")}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      value={selectedItem.path}
                      onChange={(event) =>
                        updateSelectedVersion(group, event.target.value)
                      }
                      className="h-9 rounded-2xl border border-input bg-background/70 px-3 text-sm"
                    >
                      {group.items.map((item) => (
                        <option key={item.path} value={item.path}>
                          {item.version}
                        </option>
                      ))}
                      <option value="__new__">+ Nueva version</option>
                    </select>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => navigateToEditor(selectedItem.path)}
                    >
                      Editar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => removeSpec(selectedItem.path)}
                      disabled={isBusy}
                    >
                      Eliminar
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
          <Button
            variant="secondary"
            size="sm"
            className="w-full"
            onClick={loadSpecs}
            disabled={isBusy}
          >
            Refresh list
          </Button>
        </CardContent>
      </Card>
    </section>
  );
}
