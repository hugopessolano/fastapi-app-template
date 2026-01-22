"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { fetchJson } from "@/lib/scaffold-api";
import { cn } from "@/lib/utils";
import { useScaffoldStatus } from "@/components/scaffold-status";

type DirectoryEntry = {
  name: string;
  path: string;
};

type BrowsePayload = {
  root: string;
  path: string;
  parent: string | null;
  directories: DirectoryEntry[];
};

export default function FolderPicker({
  label,
  value,
  onChange,
  helper,
  actionLabel = "Seleccionar carpeta",
  placeholder = "Selecciona una carpeta",
  isSelected,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  helper?: string;
  actionLabel?: string;
  placeholder?: string;
  isSelected?: boolean;
}) {
  const { setStatus } = useScaffoldStatus();
  const [isOpen, setIsOpen] = useState(false);
  const [browse, setBrowse] = useState<BrowsePayload | null>(null);
  const [currentPath, setCurrentPath] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setCurrentPath(value || "");
  }, [isOpen, value]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    const load = async () => {
      try {
        setIsBusy(true);
        const url = currentPath
          ? `/projects/browse?path=${encodeURIComponent(currentPath)}`
          : "/projects/browse";
        const data = await fetchJson(url);
        setBrowse(data);
      } catch (error) {
        setStatus({ tone: "error", message: String(error) });
      } finally {
        setIsBusy(false);
      }
    };
    load();
  }, [currentPath, isOpen, setStatus]);

  const selectCurrent = () => {
    onChange(currentPath);
    setIsOpen(false);
  };

  const selected = isSelected ?? Boolean(value);
  const displayValue = selected
    ? value && value !== "." ? `/${value}` : "/"
    : placeholder;

  return (
    <div className="space-y-2">
      <div className="text-xs font-semibold uppercase text-muted-foreground">
        {label}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex-1 rounded-2xl border border-border/60 bg-background/70 px-3 py-2 text-sm text-muted-foreground">
          {displayValue}
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setIsOpen((current) => !current)}
        >
          {isOpen ? "Cerrar" : actionLabel}
        </Button>
      </div>
      {helper ? (
        <p className="text-xs text-muted-foreground">{helper}</p>
      ) : null}

      {isOpen ? (
        <div className="rounded-3xl border border-border/60 bg-background/70 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
            <div>
              Raiz: {browse?.root ?? "-"}
              {browse?.path ? ` / ${browse.path}` : ""}
            </div>
            <div className="flex items-center gap-2">
              {browse?.parent ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentPath(browse.parent ?? "")}
                >
                  Subir
                </Button>
              ) : null}
              <Button
                size="sm"
                onClick={selectCurrent}
                disabled={isBusy}
              >
                Usar esta carpeta
              </Button>
            </div>
          </div>
          <div className="mt-4 space-y-2">
            {browse?.directories.length ? (
              browse.directories.map((entry) => (
                <button
                  key={entry.path}
                  type="button"
                  onClick={() => setCurrentPath(entry.path)}
                  className={cn(
                    "w-full rounded-2xl border border-border/60 px-3 py-2 text-left text-sm text-foreground hover:bg-muted/40"
                  )}
                >
                  {entry.name}
                </button>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-border/60 px-3 py-4 text-xs text-muted-foreground">
                No hay carpetas para mostrar.
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
