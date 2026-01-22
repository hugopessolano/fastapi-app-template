"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ProjectEmptyState({
  title = "Selecciona una API",
  description = "Para continuar, elige una API existente o crea una nueva.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <section className="mx-auto flex max-w-2xl flex-col gap-4">
      <div className="rounded-3xl border border-dashed border-border/70 bg-background/60 p-6 text-center">
        <h1 className="text-balance text-2xl font-semibold text-foreground">
          {title}
        </h1>
        <p className="mt-2 text-pretty text-sm text-muted-foreground">
          {description}
        </p>
        <Button asChild className="mt-4">
          <Link href="/projects">Ir a proyectos</Link>
        </Button>
      </div>
    </section>
  );
}
