import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import ProjectsPage from "../projects/page";
import { ScaffoldStatusProvider } from "../../components/scaffold-status";
import { ProjectProvider } from "../../components/project-context";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const demoProjects = [
  { id: "demo", name: "Demo API", path: "/tmp/demo" },
  { id: "second", name: "Second API", path: "/tmp/second" },
];

const renderWithProviders = (ui: ReactElement, activeId = "demo") =>
  render(
    <ScaffoldStatusProvider>
      <ProjectProvider initialProjects={demoProjects} initialActiveId={activeId}>
        {ui}
      </ProjectProvider>
    </ScaffoldStatusProvider>
  );

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ projects: demoProjects }),
  }));
});

describe("ProjectsPage", () => {
  it("renders the projects heading", () => {
    renderWithProviders(<ProjectsPage />);
    expect(screen.getByText("Proyectos")).toBeInTheDocument();
    expect(screen.getByText("Crear nueva API")).toBeInTheDocument();
    expect(screen.getByText("Abrir API existente")).toBeInTheDocument();
  });

  it("shows registered projects", () => {
    renderWithProviders(<ProjectsPage />);
    expect(screen.getByText("Demo API")).toBeInTheDocument();
    expect(screen.getByText("Second API")).toBeInTheDocument();
    expect(screen.getAllByText("Abrir").length).toBeGreaterThan(0);
  });
});
