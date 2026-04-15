"use client";

import { Bell, Search, Settings, User } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface TopBarProps {
  title: string;
}

export function TopBar({ title }: TopBarProps) {
  return (
    <header className="bg-surface flex h-16 shrink-0 items-center gap-4 px-8">
      <div className="font-heading text-primary text-sm font-semibold tracking-wide uppercase">
        {title}
      </div>
      <div className="relative ml-6 max-w-sm flex-1">
        <Search className="text-on-surface-variant pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
        <Input placeholder="Search buildings…" className="h-10 pl-9" />
      </div>
      <div className="ml-auto flex items-center gap-1">
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Settings">
          <Settings />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Account">
          <User />
        </Button>
      </div>
    </header>
  );
}
