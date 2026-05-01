"use client";

import * as React from "react";

const STORAGE_KEY = "buildingpulse:unlocked-reports";

export type UnlockState = {
  unlocked: ReadonlyArray<string>;
};

export type UnlockAction =
  | { type: "unlock"; reportId: string }
  | { type: "hydrate"; reportIds: ReadonlyArray<string> }
  | { type: "reset" };

export const initialUnlockState: UnlockState = { unlocked: [] };

export function unlockReducer(state: UnlockState, action: UnlockAction): UnlockState {
  switch (action.type) {
    case "unlock": {
      if (state.unlocked.includes(action.reportId)) return state;
      return { unlocked: [...state.unlocked, action.reportId] };
    }
    case "hydrate": {
      return { unlocked: [...action.reportIds] };
    }
    case "reset": {
      if (state.unlocked.length === 0) return state;
      return { unlocked: [] };
    }
  }
}

interface UnlockContextValue {
  isUnlocked: (reportId: string) => boolean;
  unlock: (reportId: string) => void;
  reset: () => void;
}

const UnlockContext = React.createContext<UnlockContextValue | null>(null);

function readSession(): ReadonlyArray<string> {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((v): v is string => typeof v === "string");
  } catch {
    return [];
  }
}

function writeSession(ids: ReadonlyArray<string>): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    // ignore
  }
}

export function UnlockProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = React.useReducer(unlockReducer, initialUnlockState);

  React.useEffect(() => {
    const ids = readSession();
    if (ids.length > 0) dispatch({ type: "hydrate", reportIds: ids });
  }, []);

  React.useEffect(() => {
    writeSession(state.unlocked);
  }, [state.unlocked]);

  const value = React.useMemo<UnlockContextValue>(
    () => ({
      isUnlocked: (reportId: string) => state.unlocked.includes(reportId),
      unlock: (reportId: string) => dispatch({ type: "unlock", reportId }),
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
