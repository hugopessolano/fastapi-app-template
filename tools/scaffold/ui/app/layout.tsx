import type { Metadata } from "next";
import { Fraunces, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { ScaffoldStatusProvider } from "@/components/scaffold-status";
import { ProjectProvider } from "@/components/project-context";
import ScaffoldFrame from "@/components/scaffold-frame";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-sans",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Scaffold Studio",
  description: "Admin UI for scaffold specs and endpoints.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${spaceGrotesk.variable} ${fraunces.variable} antialiased font-sans`}
      >
        <ScaffoldStatusProvider>
          <ProjectProvider>
            <ScaffoldFrame>{children}</ScaffoldFrame>
          </ProjectProvider>
        </ScaffoldStatusProvider>
      </body>
    </html>
  );
}
