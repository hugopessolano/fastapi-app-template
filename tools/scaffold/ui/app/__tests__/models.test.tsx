import type { ReactElement } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import ModelEditor from "../models/page";
import { ScaffoldStatusProvider } from "../../components/scaffold-status";
import { ProjectProvider } from "../../components/project-context";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const demoProject = {
  id: "demo",
  name: "Demo API",
  path: "/tmp/demo",
};

const renderWithStatus = (ui: ReactElement) =>
  render(
    <ScaffoldStatusProvider>
      <ProjectProvider initialProjects={[demoProject]} initialActiveId="demo">
        {ui}
      </ProjectProvider>
    </ScaffoldStatusProvider>
  );

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ specs: [] }),
  }));
});

describe("ModelEditor", () => {
  it("renders the model editor heading", async () => {
    renderWithStatus(<ModelEditor />);
    expect(await screen.findByText("Modelos")).toBeInTheDocument();
    expect(screen.getByText("Volver a endpoints")).toBeInTheDocument();
  });

  it("loads a spec and shows model fields", async () => {
    const spec = {
      version: "v1",
      name: "widget",
      plural: "widgets",
      table_name: "widgets",
      tags: ["Widgets"],
      auth_required: true,
      tenant_scoped: false,
      soft_delete: true,
      pagination: true,
      ordering: true,
      fields: [
        { name: "name", type: "String", nullable: false, unique: false },
      ],
      relations: [],
      endpoints: {
        list: true,
        get: true,
        create: true,
        update: true,
        delete: true,
      },
      tests: { enabled: true },
    };

    const fetchMock = vi.fn(async (input) => {
      const url = String(input);
      if (url.includes("/specs/read")) {
        return { ok: true, json: async () => ({ spec }) };
      }
      if (url.endsWith("/specs")) {
        return {
          ok: true,
          json: async () => ({
            specs: [{ path: "specs/widgets.json", name: "widget" }],
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    vi.stubGlobal("fetch", fetchMock);

    renderWithStatus(<ModelEditor />);

    const editButton = await screen.findByText("Editar");
    fireEvent.click(editButton);

    expect(await screen.findByText("Campos")).toBeInTheDocument();
  });

  it("keeps focus while editing a field name", async () => {
    const spec = {
      version: "v1",
      name: "widget",
      plural: "widgets",
      table_name: "widgets",
      tags: ["Widgets"],
      auth_required: true,
      tenant_scoped: false,
      soft_delete: true,
      pagination: true,
      ordering: true,
      fields: [
        { name: "name", type: "String", nullable: false, unique: false },
      ],
      relations: [],
      endpoints: {
        list: true,
        get: true,
        create: true,
        update: true,
        delete: true,
      },
      tests: { enabled: true },
    };

    const fetchMock = vi.fn(async (input) => {
      const url = String(input);
      if (url.includes("/specs/read")) {
        return { ok: true, json: async () => ({ spec }) };
      }
      if (url.endsWith("/specs")) {
        return {
          ok: true,
          json: async () => ({
            specs: [{ path: "specs/widgets.json", name: "widget" }],
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });

    vi.stubGlobal("fetch", fetchMock);

    renderWithStatus(<ModelEditor />);

    const editButton = await screen.findByText("Editar");
    fireEvent.click(editButton);

    const input = (await screen.findByDisplayValue("name")) as HTMLInputElement;
    input.focus();
    expect(document.activeElement).toBe(input);

    fireEvent.change(input, { target: { value: "name2" } });
    const updatedInput = (await screen.findByDisplayValue("name2")) as HTMLInputElement;

    expect(document.activeElement).toBe(updatedInput);
  });
});
