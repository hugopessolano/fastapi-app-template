"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useProjects } from "@/components/project-context";
import { useScaffoldStatus } from "@/components/scaffold-status";
import { fetchJson } from "@/lib/scaffold-api";
import FolderPicker from "@/components/folder-picker";
import { Input } from "@/components/ui/input";

export default function ProjectsPage() {
  const router = useRouter();
  const { projects, activeProject, setActiveProjectId, refreshProjects } =
    useProjects();
  const { setStatus } = useScaffoldStatus();
  const [isBusy, setIsBusy] = useState(false);
  const [newName, setNewName] = useState("");
  const [basePath, setBasePath] = useState("");
  const [basePathSelected, setBasePathSelected] = useState(false);
  const [openPath, setOpenPath] = useState("");
  const [openPathSelected, setOpenPathSelected] = useState(false);
  const [openName, setOpenName] = useState("");

  const handleCreate = async () => {
    if (!newName.trim() || !basePathSelected) {
      setStatus({ tone: "error", message: "Nombre y ruta son obligatorios." });
      return;
    }
    try {
      setIsBusy(true);
      const data = await fetchJson("/projects/create", {
        method: "POST",
        body: JSON.stringify({ base_path: basePath.trim(), name: newName.trim() }),
      });
      await refreshProjects();
      setActiveProjectId(data.project?.id ?? null);
      setStatus({ tone: "success", message: "Proyecto creado." });
      router.push("/endpoints");
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const handleOpen = async () => {
    if (!openPathSelected) {
      setStatus({ tone: "error", message: "Ruta requerida para abrir la API." });
      return;
    }
    try {
      setIsBusy(true);
      const data = await fetchJson("/projects/open", {
        method: "POST",
        body: JSON.stringify({
          path: openPath.trim(),
          name: openName.trim() || undefined,
        }),
      });
      await refreshProjects();
      setActiveProjectId(data.project?.id ?? null);
      setStatus({ tone: "success", message: "Proyecto abierto." });
      router.push("/endpoints");
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    } finally {
      setIsBusy(false);
    }
  };

  const selectProject = (projectId: string) => {
    setActiveProjectId(projectId);
    router.push("/endpoints");
  };

  return (
    <section className="mx-auto flex max-w-6xl flex-col gap-6">
      <div className="space-y-2">
        <h1 className="text-balance text-2xl font-semibold sm:text-3xl">
          Proyectos
        </h1>
        <p className="text-pretty text-sm text-muted-foreground">
          Crea o abre una API para administrar endpoints, modelos y schemas.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>APIs abiertas</CardTitle>
            <CardDescription>
              Selecciona una API para continuar trabajando.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {projects.length === 0 ? (
              <div className="text-pretty rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
                Todavia no hay proyectos registrados.
              </div>
            ) : (
              projects.map((project) => (
                <div
                  key={project.id}
                  className="rounded-3xl border border-border/60 bg-background/60 p-4"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="text-base font-semibold text-foreground">
                        {project.name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {project.path}
                      </div>
                      {activeProject?.id === project.id && (
                        <div className="mt-1 text-[11px] font-medium text-primary">
                          Activo
                        </div>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => selectProject(project.id)}
                    >
                      Abrir
                    </Button>
                  </div>
                </div>
              ))
            )}
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={refreshProjects}
              disabled={isBusy}
            >
              Refresh list
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
          <CardHeader>
            <CardTitle>Crear nueva API</CardTitle>
            <CardDescription>
              Define una ruta base y el nombre del proyecto.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
              <FolderPicker
                label="Ruta base"
                value={basePath}
                onChange={(value) => {
                  setBasePath(value);
                  setBasePathSelected(true);
                }}
                helper="Selecciona la carpeta donde se creara la API."
                actionLabel="Elegir carpeta"
                isSelected={basePathSelected}
              />
              <Input
                placeholder="Nombre de la API"
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
              />
              <Button onClick={handleCreate} disabled={isBusy}>
                Crear API
              </Button>
            </CardContent>
          </Card>

          <Card>
          <CardHeader>
            <CardTitle>Abrir API existente</CardTitle>
            <CardDescription>
              Registra una API creada previamente.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
              <FolderPicker
                label="Ruta de la API"
                value={openPath}
                onChange={(value) => {
                  setOpenPath(value);
                  setOpenPathSelected(true);
                }}
                helper="Selecciona la carpeta donde vive la API."
                actionLabel="Elegir carpeta"
                isSelected={openPathSelected}
              />
              <Input
                placeholder="Nombre visible (opcional)"
                value={openName}
                onChange={(event) => setOpenName(event.target.value)}
              />
              <Button variant="secondary" onClick={handleOpen} disabled={isBusy}>
                Abrir API
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
