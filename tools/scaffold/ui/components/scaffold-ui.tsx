"use client";

import type { ReactNode } from "react";

export const toggleClass =
  "h-4 w-4 rounded border border-input bg-background text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40";

export function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <input
      type="checkbox"
      checked={checked}
      onChange={(event) => onChange(event.target.checked)}
      className={toggleClass}
    />
  );
}

export function Section({
  title,
  info,
  actions,
  children,
}: {
  title: string;
  info?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-border/60 bg-card/70 p-5">
      <div className="mb-4 flex items-center justify-between gap-3 text-xs font-semibold uppercase text-muted-foreground">
        <span>{title}</span>
        <div className="flex items-center gap-2">
          {actions}
          {info ? <InfoTip text={info} /> : null}
        </div>
      </div>
      {children}
    </div>
  );
}

export function FieldBlock({
  label,
  info,
  children,
}: {
  label: string;
  info?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2 text-xs uppercase text-muted-foreground">
        <label>{label}</label>
        {info ? <InfoTip text={info} /> : null}
      </div>
      {children}
    </div>
  );
}

export function HelperText({ children }: { children: ReactNode }) {
  return <p className="text-pretty text-xs text-muted-foreground">{children}</p>;
}

export function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-2xl border border-border/60 bg-background/60 px-3 py-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <Toggle checked={checked} onChange={onChange} />
    </label>
  );
}

export function InfoTip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex">
      <span className="flex h-5 w-5 items-center justify-center rounded-full border border-border/60 text-[10px] font-semibold text-muted-foreground">
        i
      </span>
      <span className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 w-56 -translate-x-1/2 rounded-2xl border border-border/70 bg-background/95 px-3 py-2 text-pretty text-xs normal-case text-muted-foreground opacity-0 shadow-lg group-hover:opacity-100">
        {text}
      </span>
    </span>
  );
}
