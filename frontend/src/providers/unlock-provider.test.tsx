import * as React from "react";
import { act, render, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  UNLOCK_STORAGE_KEY,
  UnlockProvider,
  initialUnlockState,
  unlockReducer,
  useUnlock,
  type UnlockState,
} from "./unlock-provider";

describe("unlockReducer", () => {
  it("adds a new reportId on unlock", () => {
    const next = unlockReducer(initialUnlockState, { type: "unlock", reportId: "r1" });
    expect(next.unlocked).toEqual(["r1"]);
  });

  it("returns the same state when unlocking an already-unlocked reportId", () => {
    const state: UnlockState = { unlocked: ["r1"] };
    const next = unlockReducer(state, { type: "unlock", reportId: "r1" });
    expect(next).toBe(state);
  });

  it("appends without dropping prior reportIds", () => {
    const state: UnlockState = { unlocked: ["r1"] };
    const next = unlockReducer(state, { type: "unlock", reportId: "r2" });
    expect(next.unlocked).toEqual(["r1", "r2"]);
  });

  it("hydrates from a list of reportIds", () => {
    const next = unlockReducer(initialUnlockState, {
      type: "hydrate",
      reportIds: ["a", "b"],
    });
    expect(next.unlocked).toEqual(["a", "b"]);
  });

  it("hydrates to an empty list", () => {
    const next = unlockReducer({ unlocked: ["x"] }, { type: "hydrate", reportIds: [] });
    expect(next.unlocked).toEqual([]);
  });

  it("clears state on reset when there is something to clear", () => {
    const next = unlockReducer({ unlocked: ["r1"] }, { type: "reset" });
    expect(next.unlocked).toEqual([]);
  });

  it("returns the same state on reset when already empty", () => {
    const next = unlockReducer(initialUnlockState, { type: "reset" });
    expect(next).toBe(initialUnlockState);
  });

});

describe("UnlockProvider", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });
  afterEach(() => {
    window.sessionStorage.clear();
  });

  function wrap(children: React.ReactNode) {
    return <UnlockProvider>{children}</UnlockProvider>;
  }

  it("starts with no reports unlocked", () => {
    const { result } = renderHook(() => useUnlock(), { wrapper: UnlockProvider });
    expect(result.current.isUnlocked("r1")).toBe(false);
  });

  it("flips isUnlocked to true after unlock() and persists to sessionStorage", () => {
    const { result } = renderHook(() => useUnlock(), { wrapper: UnlockProvider });
    act(() => result.current.unlock("r1"));
    expect(result.current.isUnlocked("r1")).toBe(true);
    expect(window.sessionStorage.getItem(UNLOCK_STORAGE_KEY)).toContain("r1");
  });

  it("hydrates from sessionStorage on mount", () => {
    window.sessionStorage.setItem(UNLOCK_STORAGE_KEY, JSON.stringify(["seeded"]));
    const { result } = renderHook(() => useUnlock(), { wrapper: UnlockProvider });
    // Effect runs after mount; assert post-effect.
    expect(result.current.isUnlocked("seeded")).toBe(true);
  });

  it("ignores malformed sessionStorage payloads", () => {
    window.sessionStorage.setItem(UNLOCK_STORAGE_KEY, "{not-json");
    const { result } = renderHook(() => useUnlock(), { wrapper: UnlockProvider });
    expect(result.current.isUnlocked("anything")).toBe(false);
  });

  it("ignores non-array JSON", () => {
    window.sessionStorage.setItem(UNLOCK_STORAGE_KEY, JSON.stringify({ not: "an array" }));
    const { result } = renderHook(() => useUnlock(), { wrapper: UnlockProvider });
    expect(result.current.isUnlocked("anything")).toBe(false);
  });

  it("reset() clears unlocked reports", () => {
    const { result } = renderHook(() => useUnlock(), { wrapper: UnlockProvider });
    act(() => result.current.unlock("r1"));
    act(() => result.current.reset());
    expect(result.current.isUnlocked("r1")).toBe(false);
  });

  it("throws when useUnlock is called outside the provider", () => {
    // Suppress React error boundary console noise from the throw.
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => renderHook(() => useUnlock())).toThrow(/useUnlock must be used/);
    spy.mockRestore();
  });

  it("renders children", () => {
    const { getByText } = render(wrap(<span>hi</span>));
    expect(getByText("hi")).toBeInTheDocument();
  });
});
