import type { ReactElement } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import ExternalDatabasesPage from "../external-dbs/page";
import { ScaffoldStatusProvider } from "../../components/scaffold-status";

const renderWithStatus = (ui: ReactElement) =>
  render(<ScaffoldStatusProvider>{ui}</ScaffoldStatusProvider>);

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ connections: [] }),
    })
  );
});

describe("ExternalDatabasesPage", () => {
  it("renders the external dbs heading", async () => {
    renderWithStatus(<ExternalDatabasesPage />);
    expect(await screen.findByText("Bases externas")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Crear conexion" })
    ).toBeInTheDocument();
  });
});
