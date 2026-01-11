import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import ModelEditor from "../models/page";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ specs: [] }),
  }));
});

describe("ModelEditor", () => {
  it("renders the model editor heading", async () => {
    render(<ModelEditor />);
    expect(
      await screen.findByText("Define modelos y relaciones con control total.")
    ).toBeInTheDocument();
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

    render(<ModelEditor />);

    const editButton = await screen.findByText("Editar");
    fireEvent.click(editButton);

    expect(await screen.findByText("Campos")).toBeInTheDocument();
  });
});
