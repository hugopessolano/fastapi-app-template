import type { ReactElement } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import SchemaEditor from "../schemas/page";
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
  window.history.pushState({}, "", "/schemas?path=specs/widgets.json");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ specs: [] }),
  }));
});

describe("SchemaEditor", () => {
  it("loads a spec and shows variant tabs", async () => {
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

    renderWithStatus(<SchemaEditor />);

    expect(await screen.findByText("Variantes")).toBeInTheDocument();
    expect(screen.getByText("create")).toBeInTheDocument();
    expect(screen.getByText("response")).toBeInTheDocument();
  });

  it("keeps focus while editing a schema field name", async () => {
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

    renderWithStatus(<SchemaEditor />);

    const input = (await screen.findByDisplayValue("name")) as HTMLInputElement;
    input.focus();
    expect(document.activeElement).toBe(input);

    fireEvent.change(input, { target: { value: "name2" } });
    const updatedInput = (await screen.findByDisplayValue("name2")) as HTMLInputElement;

    expect(document.activeElement).toBe(updatedInput);
  });

  it("hides disabled fields by default and can show them", async () => {
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

    renderWithStatus(<SchemaEditor />);

    expect(await screen.findByDisplayValue("name")).toBeInTheDocument();

    fireEvent.click(await screen.findByRole("button", { name: "Remove" }));

    await waitFor(() =>
      expect(screen.queryByDisplayValue("name")).not.toBeInTheDocument()
    );

    const toggle = screen.getByLabelText("Mostrar deshabilitados");
    fireEvent.click(toggle);

    expect(await screen.findByDisplayValue("name")).toBeInTheDocument();
  });

  it("syncs fields only for the active variant when toggle is off", async () => {
    const baseSpec = {
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
    };

    const updatedSpec = {
      ...baseSpec,
      fields: [
        ...baseSpec.fields,
        { name: "status", type: "String", nullable: false, unique: false },
      ],
    };

    let readCount = 0;
    const fetchMock = vi.fn(async (input) => {
      const url = String(input);
      if (url.includes("/specs/read")) {
        readCount += 1;
        const spec = readCount < 3 ? baseSpec : updatedSpec;
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

    renderWithStatus(<SchemaEditor />);

    expect(await screen.findByDisplayValue("name")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("status")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Sincronizar campos" }));

    expect(await screen.findByDisplayValue("status")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "update" }));
    await waitFor(() =>
      expect(screen.queryByDisplayValue("status")).not.toBeInTheDocument()
    );
  });

  it("syncs fields across variants when toggle is enabled", async () => {
    const baseSpec = {
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
    };

    const updatedSpec = {
      ...baseSpec,
      fields: [
        ...baseSpec.fields,
        { name: "status", type: "String", nullable: false, unique: false },
      ],
    };

    let readCount = 0;
    const fetchMock = vi.fn(async (input) => {
      const url = String(input);
      if (url.includes("/specs/read")) {
        readCount += 1;
        const spec = readCount < 3 ? baseSpec : updatedSpec;
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

    renderWithStatus(<SchemaEditor />);

    const toggle = await screen.findByLabelText("Todas las variantes");
    fireEvent.click(toggle);

    fireEvent.click(screen.getByRole("button", { name: "Sincronizar campos" }));

    expect(await screen.findByDisplayValue("status")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "update" }));
    expect(await screen.findByDisplayValue("status")).toBeInTheDocument();
  });
});
