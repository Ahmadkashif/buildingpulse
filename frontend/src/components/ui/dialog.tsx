"use client";

import * as React from "react";
import { X } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
}

/**
 * Glass modal per DESIGN.md:
 *   surface-container-lowest @ 80% + 24px backdrop-blur.
 * Kept intentionally simple — no portal, no focus trap — for scaffold purposes.
 */
function Dialog({ open, onClose, children, title, description, className }: DialogProps) {
  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <button
        type="button"
        aria-label="Close dialog"
        onClick={onClose}
        className="bg-on-surface/30 absolute inset-0 backdrop-blur-sm"
      />
      <div
        className={cn(
          "bg-card/80 text-card-foreground shadow-ambient relative w-full max-w-md rounded-2xl p-6 backdrop-blur-2xl",
          className,
        )}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            {title ? (
              <div className="font-heading text-lg leading-tight font-semibold">{title}</div>
            ) : null}
            {description ? (
              <div className="text-on-surface-variant text-sm">{description}</div>
            ) : null}
          </div>
          <Button variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close">
            <X />
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}

export { Dialog };
