import * as React from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

type SelectProps = React.ComponentProps<"select">;

function Select({ className, children, ...props }: SelectProps) {
  return (
    <div className="relative">
      <select
        data-slot="select"
        className={cn(
          "bg-input text-on-surface focus-visible:ring-ring/60 h-11 w-full appearance-none rounded-md pr-10 pl-3 text-sm transition-colors outline-none focus-visible:ring-2 disabled:opacity-60",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="text-on-surface-variant pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2" />
    </div>
  );
}

export { Select };
