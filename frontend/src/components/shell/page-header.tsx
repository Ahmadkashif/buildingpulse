import * as React from "react";

import { cn } from "@/lib/utils";

interface PageHeaderProps extends React.ComponentProps<"header"> {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ title, description, actions, className, ...props }: PageHeaderProps) {
  return (
    <header
      data-slot="page-header"
      className={cn("mb-8 flex items-end justify-between gap-6", className)}
      {...props}
    >
      <div className="flex max-w-2xl flex-col gap-1">
        <h1 className="font-heading text-on-surface text-3xl font-bold tracking-tight">{title}</h1>
        {description ? <p className="text-on-surface-variant text-sm">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </header>
  );
}
