import * as React from "react";
import { Input as InputPrimitive } from "@base-ui/react/input";

import { cn } from "@/lib/utils";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        /* Ghost fill per DESIGN.md — no borders, surface-container-high bg */
        "bg-input text-on-surface placeholder:text-on-surface-variant/70 focus-visible:ring-ring/60 h-11 w-full rounded-md px-3 py-2 text-base transition-colors outline-none focus-visible:ring-2 disabled:opacity-60 md:text-sm",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
