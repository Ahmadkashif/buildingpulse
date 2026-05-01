"use client";

import * as React from "react";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/forms/form-field";
import { useAddressLookup } from "@/hooks/use-address-lookup";
import type { AddressMatch } from "@/types";

interface AddressLookupFieldProps {
  onMatch: (match: AddressMatch) => void;
}

export function AddressLookupField({ onMatch }: AddressLookupFieldProps) {
  const [address, setAddress] = React.useState("");
  const lookup = useAddressLookup();

  const submit = () => {
    if (!address.trim() || lookup.isPending) return;
    lookup.mutate(address.trim(), {
      onSuccess: (record) => {
        onMatch(record);
      },
    });
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      submit();
    }
  };

  const status = ((): React.ReactNode => {
    if (lookup.isPending) {
      return (
        <span data-testid="address-lookup-status" className="text-on-surface-variant text-xs">
          Looking up address…
        </span>
      );
    }
    if (lookup.isSuccess && lookup.data) {
      return (
        <span data-testid="address-lookup-status" className="text-secondary text-xs">
          Match found: {lookup.data.addressNormalized} — fields auto-filled. You can edit them
          below.
        </span>
      );
    }
    if (lookup.isError) {
      const isMiss = lookup.error?.kind === "miss";
      return (
        <span data-testid="address-lookup-status" className="text-destructive text-xs">
          {isMiss
            ? "We couldn't find that address. Enter your building details manually below."
            : "Address lookup failed. Enter your building details manually below."}
        </span>
      );
    }
    return null;
  })();

  return (
    <FormField
      label="Look up by address"
      htmlFor="address-lookup"
      hint="Optional — auto-fills the form from NYC LL84 data."
      data-testid="address-lookup-field"
    >
      <div className="flex items-stretch gap-2">
        <div className="relative flex-1">
          <Input
            id="address-lookup"
            type="text"
            placeholder="e.g. 100 Synth St"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            onKeyDown={onKeyDown}
            className="pl-9"
            data-testid="address-lookup-input"
          />
          <Search className="text-on-surface-variant pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2" />
        </div>
        <Button
          type="button"
          variant="secondary"
          onClick={submit}
          disabled={!address.trim() || lookup.isPending}
          data-testid="address-lookup-submit"
        >
          {lookup.isPending ? "Searching…" : "Look up"}
        </Button>
      </div>
      {status}
    </FormField>
  );
}
