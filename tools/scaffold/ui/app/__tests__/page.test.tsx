import { render, screen } from "@testing-library/react";
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
});
