import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import EndpointsPage from "../endpoints/page";
import { ScaffoldStatusProvider } from "../../components/scaffold-status";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const renderWithStatus = (ui: ReactElement) =>
  render(<ScaffoldStatusProvider>{ui}</ScaffoldStatusProvider>);

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ specs: [] }),
  }));
});

describe("EndpointsPage", () => {
  it("renders the main heading", async () => {
    renderWithStatus(<EndpointsPage />);
    expect(await screen.findByText("Endpoints")).toBeInTheDocument();
    expect(screen.getByText("Nuevo endpoint")).toBeInTheDocument();
    expect(screen.getByText("Listado")).toBeInTheDocument();
  });

  it("loads specs and shows edit actions", async () => {
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
      fields: [{ name: "name", type: "String", nullable: false, unique: false }],
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

    renderWithStatus(<EndpointsPage />);

    expect(await screen.findByText("Editar")).toBeInTheDocument();
    expect(screen.getByText("Eliminar")).toBeInTheDocument();
  });
});
