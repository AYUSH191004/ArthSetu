import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { User } from "@/types/api";

const meMock = vi.fn();
const loginMock = vi.fn();

vi.mock("@/api/endpoints", () => ({
  authApi: {
    me: () => meMock(),
    login: (u: string, p: string) => loginMock(u, p),
  },
}));

import { AuthProvider, useAuth } from "./AuthContext";

const reviewer: User = {
  id: "1",
  username: "rev",
  full_name: "Reviewer",
  email: null,
  role: "reviewer",
  is_active: true,
  created_at: null,
};

function Probe() {
  const { user, loading, login, can } = useAuth();
  if (loading) return <span>loading</span>;
  return (
    <div>
      <span data-testid="user">{user ? user.username : "anon"}</span>
      <span data-testid="can-viewer">{String(can("viewer"))}</span>
      <span data-testid="can-reviewer">{String(can("reviewer"))}</span>
      <span data-testid="can-admin">{String(can("admin"))}</span>
      <button onClick={() => login("rev", "pw")}>login</button>
    </div>
  );
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    meMock.mockReset();
    loginMock.mockReset();
    localStorage.clear();
  });

  it("starts anonymous when there is no token", async () => {
    renderProbe();
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anon"));
    expect(meMock).not.toHaveBeenCalled();
  });

  it("hydrates the user from /me when a token exists", async () => {
    localStorage.setItem("arthsetu.token", "tok");
    meMock.mockResolvedValue(reviewer);
    renderProbe();
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("rev"));
  });

  it("clears a bad token", async () => {
    localStorage.setItem("arthsetu.token", "stale");
    meMock.mockRejectedValue(new Error("401"));
    renderProbe();
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anon"));
    expect(localStorage.getItem("arthsetu.token")).toBeNull();
  });

  it("login stores the token and sets the user", async () => {
    loginMock.mockResolvedValue({ access_token: "new-tok", user: reviewer });
    renderProbe();
    await waitFor(() => screen.getByText("login"));
    await userEvent.click(screen.getByText("login"));
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("rev"));
    expect(localStorage.getItem("arthsetu.token")).toBe("new-tok");
  });

  it("can() respects the role hierarchy", async () => {
    localStorage.setItem("arthsetu.token", "tok");
    meMock.mockResolvedValue(reviewer);
    renderProbe();
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("rev"));
    expect(screen.getByTestId("can-viewer")).toHaveTextContent("true");
    expect(screen.getByTestId("can-reviewer")).toHaveTextContent("true");
    expect(screen.getByTestId("can-admin")).toHaveTextContent("false");
  });
});
