import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import SettingsPage from "../settings/page";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ settings: { AUTH_MODE: "built_in" } }),
    })
  );
});

describe("SettingsPage", () => {
  it("renders the settings header", async () => {
    render(<SettingsPage />);
    expect(
      await screen.findByText("Configuracion general")
    ).toBeInTheDocument();
    expect(screen.getByText("Defaults globales")).toBeInTheDocument();
  });
});
