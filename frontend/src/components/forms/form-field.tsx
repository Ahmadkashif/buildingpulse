import * as React from "react";

import { cn } from "@/lib/utils";

interface FormFieldProps extends React.ComponentProps<"div"> {
  label: string;
  /** Helper text shown below the control (e.g. accepted range). */
  hint?: string;
  htmlFor?: string;
}

export function FormField({ label, hint, htmlFor, className, children, ...props }: FormFieldProps) {
  return (
    <div data-slot="form-field" className={cn("flex flex-col gap-2", className)} {...props}>
      <label htmlFor={htmlFor} className="text-label-md text-on-surface-variant">
        {label}
      </label>
      {children}
      {hint ? <span className="text-on-surface-variant text-xs">{hint}</span> : null}
    </div>
  );
}
