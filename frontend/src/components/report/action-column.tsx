import * as React from "react";

import { cn } from "@/lib/utils";

type ActionColumnProps = React.ComponentProps<"aside">;

/** Right-side vertical CTA stack used on the report page. */
export function ActionColumn({ className, children, ...props }: ActionColumnProps) {
  return (
    <aside data-slot="action-column" className={cn("flex flex-col gap-3", className)} {...props}>
      {children}
    </aside>
  );
}
