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
  it("renders the main heading", () => {
    render(<ScaffoldStudio />);
    expect(
      screen.getByText("Administra specs, modelos y routers desde un mismo panel.")
    ).toBeInTheDocument();
  });
});
