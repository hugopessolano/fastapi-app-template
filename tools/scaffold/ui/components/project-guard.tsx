"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useProjects } from "@/components/project-context";

export function useRequireProject() {
  const router = useRouter();
  const { activeProject } = useProjects();

  useEffect(() => {
    if (!activeProject) {
      router.replace("/projects");
    }
  }, [activeProject, router]);

  return activeProject;
}
