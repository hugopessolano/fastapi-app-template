import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import SettingsPage from "../settings/page";
import { ScaffoldStatusProvider } from "../../components/scaffold-status";

const renderWithStatus = (ui: ReactElement) =>
  render(<ScaffoldStatusProvider>{ui}</ScaffoldStatusProvider>);

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
    renderWithStatus(<SettingsPage />);
    expect(await screen.findByText("Configuraciones")).toBeInTheDocument();
    expect(screen.getByText("Defaults globales")).toBeInTheDocument();
  });
});
