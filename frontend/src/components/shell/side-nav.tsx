"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Building2,
  LayoutDashboard,
  LineChart,
  LifeBuoy,
  LogOut,
  Settings,
  Sparkles,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const PRIMARY_NAV: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Forecasting", href: "/forecasting", icon: Activity },
  { label: "Energy Insights", href: "/insights", icon: LineChart },
  { label: "Building Assets", href: "/assets", icon: Building2 },
  { label: "Reports", href: "/reports", icon: BarChart3 },
];

const FOOTER_NAV: NavItem[] = [
  { label: "Settings", href: "/settings", icon: Settings },
  { label: "Support", href: "/support", icon: LifeBuoy },
  { label: "Sign Out", href: "/sign-out", icon: LogOut },
];

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

export function SideNav() {
  const pathname = usePathname();

  return (
    <aside className="bg-sidebar flex w-64 shrink-0 flex-col">
      <div className="flex flex-col gap-1 px-6 pt-6 pb-8">
        <div className="flex items-center gap-2">
          <div className="bg-signature text-primary-foreground grid size-7 place-items-center rounded-md">
            <Sparkles className="size-4" />
          </div>
          <span className="font-heading text-primary text-base font-bold tracking-tight">
            buildingPulse
          </span>
        </div>
        <span className="text-label-sm text-on-surface-variant">Energy Management</span>
      </div>

      <nav aria-label="Primary" className="flex flex-1 flex-col gap-0.5 px-3">
        {PRIMARY_NAV.map((item) => {
          const Icon = item.icon;
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold tracking-wide uppercase transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-on-surface-variant hover:bg-sidebar-accent/60",
              )}
            >
              {active ? (
                <span
                  aria-hidden
                  className="bg-primary absolute top-2 bottom-2 left-0 w-1 rounded-r-full"
                />
              ) : null}
              <Icon className="size-4" />
              <span className="text-xs">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="flex flex-col gap-2 px-6 py-6">
        <Link
          href="/forecasting"
          className={buttonVariants({ variant: "gradient", width: "full" })}
        >
          Generate Forecast
        </Link>
        <div className="mt-4 flex flex-col gap-0.5">
          {FOOTER_NAV.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="text-on-surface-variant hover:bg-sidebar-accent/60 flex items-center gap-3 rounded-md px-2 py-2 text-xs font-semibold tracking-wide uppercase"
              >
                <Icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
