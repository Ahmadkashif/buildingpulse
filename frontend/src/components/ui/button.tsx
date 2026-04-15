"use client";

import { Button as ButtonPrimitive } from "@base-ui/react/button";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all outline-none select-none focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        /** Primary gradient CTA — DESIGN.md signature gradient. */
        gradient:
          "bg-signature text-primary-foreground shadow-ambient hover:brightness-110 active:brightness-95",
        /** Solid primary — flat primary fill. */
        default: "bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary",
        /** Filled container — surface-container-highest with primary text. */
        secondary: "bg-surface-container-highest text-primary hover:bg-surface-container-high",
        /** Ghost — transparent, primary text, subtle hover fill. */
        tertiary: "bg-transparent text-primary hover:bg-surface-container-high/60",
        /** Low-emphasis ghost for icons/menus. */
        ghost: "hover:bg-surface-container-high text-on-surface",
        /** Destructive tonal chip. */
        destructive: "bg-destructive-container text-on-destructive-container hover:brightness-105",
        /** Link-styled. */
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-6",
        xl: "h-12 px-8 text-base",
        icon: "size-10",
        "icon-sm": "size-8",
      },
      width: {
        auto: "",
        full: "w-full",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      width: "auto",
    },
  },
);

function Button({
  className,
  variant,
  size,
  width,
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, width, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
