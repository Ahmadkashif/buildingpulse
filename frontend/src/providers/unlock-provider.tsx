"use client";

import * as React from "react";

const STORAGE_KEY = "buildingpulse:unlocked-reports";

export type UnlockEntry = { reportId: string; email: string | null };

export type UnlockState = {
  unlocked: ReadonlyArray<UnlockEntry>;
};

export type UnlockAction =
  | { type: "unlock"; reportId: string; email: string | null }
  | { type: "hydrate"; entries: ReadonlyArray<UnlockEntry> }
  | { type: "reset" };

export const initialUnlockState: UnlockState = { unlocked: [] };

export function unlockReducer(state: UnlockState, action: UnlockAction): UnlockState {
  switch (action.type) {
    case "unlock": {
      const existingIdx = state.unlocked.findIndex((e) => e.reportId === action.reportId);
      const next: UnlockEntry = { reportId: action.reportId, email: action.email };
      if (existingIdx === -1) return { unlocked: [...state.unlocked, next] };
      const merged = [...state.unlocked];
      merged[existingIdx] = { ...merged[existingIdx]!, email: action.email ?? merged[existingIdx]!.email };
      return { unlocked: merged };
    }
    case "hydrate": {
      return { unlocked: [...action.entries] };
    }
    case "reset": {
      if (state.unlocked.length === 0) return state;
      return { unlocked: [] };
    }
  }
}

interface UnlockContextValue {
  isUnlocked: (reportId: string) => boolean;
  emailFor: (reportId: string) => string | null;
  unlock: (reportId: string, email?: string | null) => void;
  reset: () => void;
}

const UnlockContext = React.createContext<UnlockContextValue | null>(null);

function readSession(): ReadonlyArray<UnlockEntry> {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.flatMap((v): UnlockEntry[] => {
      if (typeof v === "string") return [{ reportId: v, email: null }];
      if (
        v &&
        typeof v === "object" &&
        typeof (v as { reportId?: unknown }).reportId === "string"
      ) {
        const obj = v as { reportId: string; email?: unknown };
        return [{ reportId: obj.reportId, email: typeof obj.email === "string" ? obj.email : null }];
      }
      return [];
    });
  } catch {
    return [];
  }
}

function writeSession(entries: ReadonlyArray<UnlockEntry>): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // ignore
  }
}

export function UnlockProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = React.useReducer(unlockReducer, initialUnlockState);

  React.useEffect(() => {
    const entries = readSession();
    if (entries.length > 0) dispatch({ type: "hydrate", entries });
  }, []);

  React.useEffect(() => {
    writeSession(state.unlocked);
  }, [state.unlocked]);

  const value = React.useMemo<UnlockContextValue>(
    () => ({
      isUnlocked: (reportId: string) => state.unlocked.some((e) => e.reportId === reportId),
      emailFor: (reportId: string) =>
        state.unlocked.find((e) => e.reportId === reportId)?.email ?? null,
      unlock: (reportId: string, email: string | null = null) =>
        dispatch({ type: "unlock", reportId, email }),
      reset: () => dispatch({ type: "reset" }),
    }),
    [state.unlocked],
  );

  return <UnlockContext.Provider value={value}>{children}</UnlockContext.Provider>;
}

export function useUnlock(): UnlockContextValue {
  const ctx = React.useContext(UnlockContext);
  if (!ctx) throw new Error("useUnlock must be used inside <UnlockProvider />");
  return ctx;
}

export const UNLOCK_STORAGE_KEY = STORAGE_KEY;
