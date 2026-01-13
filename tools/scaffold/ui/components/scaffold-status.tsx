"use client";

import { createContext, useContext, useMemo, useState } from "react";
import type { StatusState } from "@/lib/specs";

type StatusContextValue = {
  status: StatusState;
  setStatus: (status: StatusState) => void;
};

const StatusContext = createContext<StatusContextValue | null>(null);

const defaultStatus: StatusState = { tone: "idle", message: "Ready." };

export function ScaffoldStatusProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [status, setStatus] = useState<StatusState>(defaultStatus);
  const value = useMemo(() => ({ status, setStatus }), [status]);
  return <StatusContext.Provider value={value}>{children}</StatusContext.Provider>;
}

export function useScaffoldStatus() {
  const context = useContext(StatusContext);
  if (!context) {
    throw new Error("useScaffoldStatus must be used within ScaffoldStatusProvider");
  }
  return context;
}
