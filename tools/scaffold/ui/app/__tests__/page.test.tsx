import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import ScaffoldStudio from "../page";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ specs: [] }),
  }));
});

describe("ScaffoldStudio", () => {
  it("renders the main heading", async () => {
    render(<ScaffoldStudio />);
    expect(
      await screen.findByText(
        "Administra endpoints y versiones con un flujo claro."
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Nuevo endpoint")).toBeInTheDocument();
  });

  it("loads a spec without relations safely", async () => {
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

    render(<ScaffoldStudio />);

    const editButton = await screen.findByText("Editar");
    fireEvent.click(editButton);

    expect(await screen.findByText("Relaciones")).toBeInTheDocument();
  });
});
