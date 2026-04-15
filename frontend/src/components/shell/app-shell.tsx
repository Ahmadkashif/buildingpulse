"use client";

import { usePathname } from "next/navigation";

import { SideNav } from "@/components/shell/side-nav";
import { TopBar } from "@/components/shell/top-bar";

const SECTION_TITLES: Record<string, string> = {
  "/": "Portfolio Dashboard",
  "/forecasting": "NYC Energy Forecast",
  "/insights": "Energy Insights",
  "/assets": "Building Assets",
  "/reports": "Reports",
};

function resolveTitle(pathname: string) {
  const match = Object.keys(SECTION_TITLES)
    .filter((key) => key !== "/")
    .find((key) => pathname.startsWith(key));
  if (match) return SECTION_TITLES[match]!;
  return SECTION_TITLES["/"]!;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const title = resolveTitle(pathname);

  return (
    <div className="bg-surface flex min-h-screen">
      <SideNav />
      <div className="flex min-h-screen flex-1 flex-col">
        <TopBar title={title} />
        <main className="flex-1 px-8 pt-4 pb-16">{children}</main>
      </div>
    </div>
  );
}
