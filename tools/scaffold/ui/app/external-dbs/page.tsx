"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ExternalDatabasesPage() {
  return (
    <section className="mx-auto flex max-w-5xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <Button asChild variant="ghost" size="sm" className="gap-2">
          <Link href="/endpoints">
            <ArrowLeft className="h-4 w-4" />
            Volver a endpoints
          </Link>
        </Button>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          Bases externas
        </h1>
        <p className="text-sm text-muted-foreground">
          Configura multiples conexiones externas desde esta vista.
        </p>
      </div>

      <Card className="animate-fade-up">
        <CardHeader>
          <CardTitle>Proximamente</CardTitle>
          <CardDescription>
            Esta pantalla se completara cuando integremos el flujo de conexiones externas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-2xl border border-dashed border-border/70 px-4 py-6 text-sm text-muted-foreground">
            Placeholder para la configuracion de bases externas.
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
