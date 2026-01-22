"use client";

import { usePathname } from "next/navigation";
import ScaffoldShell from "@/components/scaffold-shell";

export default function ScaffoldFrame({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  if (pathname.startsWith("/projects")) {
    return <div className="min-h-dvh px-6 py-8 sm:px-10">{children}</div>;
  }
  return <ScaffoldShell>{children}</ScaffoldShell>;
}
