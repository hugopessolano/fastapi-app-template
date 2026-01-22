import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import EndpointEditorPage from "../endpoints/editor/page";
import { ScaffoldStatusProvider } from "../../components/scaffold-status";
import { ProjectProvider } from "../../components/project-context";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
  useRouter: () => ({ replace: vi.fn() }),
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
  window.history.pushState(
    {},
    "",
    "/endpoints/editor?path=specs%252Fwidgets.json"
  );
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ specs: [] }),
  }));
});

describe("EndpointEditorPage", () => {
  it("loads an encoded spec path and shows the editor", async () => {
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
      external_dbs: [],
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
      if (url.includes("/external-dbs")) {
        return { ok: true, json: async () => ({ connections: [] }) };
      }
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

    renderWithStatus(<EndpointEditorPage />);

    expect(
      await screen.findByDisplayValue("specs/widgets.json")
    ).toBeInTheDocument();
    expect(await screen.findByText("Editar endpoint")).toBeInTheDocument();
  });
});
