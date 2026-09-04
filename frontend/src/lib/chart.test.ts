import { describe, expect, it } from "vitest";
import { STATUS_COLOR, STATUS_ORDER, shortMonth } from "./chart";

describe("shortMonth", () => {
  it("formats YYYY-MM to a short label", () => {
    expect(shortMonth("2026-07")).toBe("Jul '26");
    expect(shortMonth("2025-01")).toBe("Jan '25");
  });
  it("passes through unparseable input", () => {
    expect(shortMonth("garbage")).toBe("garbage");
  });
});

describe("status palette", () => {
  it("has a colour for every ordered status", () => {
    for (const key of STATUS_ORDER) {
      expect(STATUS_COLOR[key]).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });
  it("orders active first and unknown last", () => {
    expect(STATUS_ORDER[0]).toBe("active");
    expect(STATUS_ORDER.at(-1)).toBe("unknown");
  });
});
