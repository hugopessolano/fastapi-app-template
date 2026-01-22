"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { fetchJson } from "@/lib/scaffold-api";
import { useScaffoldStatus } from "@/components/scaffold-status";

export type ProjectInfo = {
  id: string;
  name: string;
  path: string;
};

type ProjectContextValue = {
  projects: ProjectInfo[];
  activeProject: ProjectInfo | null;
  setActiveProjectId: (projectId: string | null) => void;
  refreshProjects: () => Promise<void>;
};

const ProjectContext = createContext<ProjectContextValue | null>(null);
const storageKey = "scaffold.activeProject";

export function ProjectProvider({
  children,
  initialProjects,
  initialActiveId,
}: {
  children: React.ReactNode;
  initialProjects?: ProjectInfo[];
  initialActiveId?: string | null;
}) {
  const { setStatus } = useScaffoldStatus();
  const [projects, setProjects] = useState<ProjectInfo[]>(initialProjects ?? []);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(
    initialActiveId ?? null
  );
  const [hasLoaded, setHasLoaded] = useState(Boolean(initialProjects?.length));

  useEffect(() => {
    if (initialActiveId !== undefined) {
      return;
    }
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      setActiveProjectId(stored);
    }
  }, [initialActiveId]);

  const refreshProjects = useCallback(async () => {
    try {
      const data = await fetchJson("/projects");
      setProjects(data.projects ?? []);
      setHasLoaded(true);
    } catch (error) {
      setStatus({ tone: "error", message: String(error) });
    }
  }, [setStatus]);

  useEffect(() => {
    if (!hasLoaded) {
      refreshProjects();
    }
  }, [hasLoaded, refreshProjects]);

  useEffect(() => {
    if (activeProjectId) {
      localStorage.setItem(storageKey, activeProjectId);
    } else {
      localStorage.removeItem(storageKey);
    }
  }, [activeProjectId]);

  useEffect(() => {
    if (!activeProjectId) {
      return;
    }
    const exists = projects.some((project) => project.id === activeProjectId);
    if (!exists) {
      setActiveProjectId(null);
    }
  }, [activeProjectId, projects]);

  const activeProject = useMemo(
    () => projects.find((project) => project.id === activeProjectId) ?? null,
    [projects, activeProjectId]
  );

  const value = useMemo(
    () => ({
      projects,
      activeProject,
      setActiveProjectId,
      refreshProjects,
    }),
    [projects, activeProject, refreshProjects]
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProjects() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useProjects must be used within ProjectProvider");
  }
  return context;
}
