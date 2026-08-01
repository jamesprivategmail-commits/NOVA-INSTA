import React, { useState, useEffect, useCallback } from "react";
import { Search, ShieldCheck, ShieldOff, ShieldAlert, Users, FileImage, BadgeCheck, ChevronDown } from "lucide-react";

// Point this at your deployed Render API URL, e.g. "https://nova-world-api.onrender.com"
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Demo data shown until an admin token is entered — lets you preview the UI without a live backend.
const DEMO_USERS = [
  { id: "1", username: "luma.orbit", email: "luma@example.com", display_name: "Luma", is_admin: false, is_verified: true, is_banned: false, created_at: "2026-01-14T00:00:00Z" },
  { id: "2", username: "kai_drift", email: "kai@example.com", display_name: "Kai", is_admin: false, is_verified: false, is_banned: false, created_at: "2026-02-02T00:00:00Z" },
  { id: "3", username: "vera.nova", email: "vera@example.com", display_name: "Vera", is_admin: true, is_verified: true, is_banned: false, created_at: "2025-12-01T00:00:00Z" },
  { id: "4", username: "spam_acct_44", email: "spam44@example.com", display_name: "", is_admin: false, is_verified: false, is_banned: true, created_at: "2026-03-20T00:00:00Z" },
];
const DEMO_STATS = { total_users: 1284, banned_users: 12, verified_users: 96, total_posts: 5391 };

function Badge({ children, tone }) {
  const tones = {
    danger: { bg: "rgba(255,79,163,0.12)", fg: "#FF4FA3" },
    ok: { bg: "rgba(51,214,192,0.12)", fg: "#33D6C0" },
    neutral: { bg: "rgba(139,133,160,0.12)", fg: "#8B85A0" },
    gold: { bg: "rgba(245,200,76,0.14)", fg: "#F5C84C" },
  };
  const t = tones[tone] || tones.neutral;
  return (
    <span style={{ background: t.bg, color: t.fg, fontSize: 11, fontWeight: 600, padding: "3px 9px", borderRadius: 99, letterSpacing: "0.02em" }}>
      {children}
    </span>
  );
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div style={{ background: "#171227", border: "1px solid #241d38", borderRadius: 14, padding: "16px 18px", flex: 1, minWidth: 140 }}>
      <Icon size={18} color="#F5C84C" />
      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 24, color: "#F2EEFA", marginTop: 10 }}>{value}</div>
      <div style={{ fontSize: 12, color: "#8B85A0", marginTop: 2 }}>{label}</div>
    </div>
  );
}

export default function AdminDashboard() {
  const [token, setToken] = useState("");
  const [tokenInput, setTokenInput] = useState("");
  const [users, setUsers] = useState(DEMO_USERS);
  const [stats, setStats] = useState(DEMO_STATS);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [demoMode, setDemoMode] = useState(true);

  const authedFetch = useCallback(
    (path, opts = {}) =>
      fetch(`${API_BASE_URL}${path}`, {
        ...opts,
        headers: { ...(opts.headers || {}), Authorization: `Bearer ${token}` },
      }),
    [token]
  );

  const loadAll = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      if (filter === "banned") params.set("banned_only", "true");
      if (filter === "unverified") params.set("unverified_only", "true");

      const [usersRes, statsRes] = await Promise.all([
        authedFetch(`/admin/users?${params.toString()}`),
        authedFetch(`/admin/stats`),
      ]);
      if (!usersRes.ok || !statsRes.ok) throw new Error("Request failed — check your token and API URL");
      setUsers(await usersRes.json());
      setStats(await statsRes.json());
      setDemoMode(false);
    } catch (e) {
      setError(e.message || "Couldn't reach the API");
    } finally {
      setLoading(false);
    }
  }, [token, query, filter, authedFetch]);

  useEffect(() => {
    if (token) loadAll();
  }, [token, filter]); // eslint-disable-line react-hooks/exhaustive-deps

  const applyToken = () => setToken(tokenInput.trim());

  const runAction = async (userId, action) => {
    if (demoMode) {
      setUsers((us) =>
        us.map((u) => {
          if (u.id !== userId) return u;
          if (action === "ban") return { ...u, is_banned: true };
          if (action === "unban") return { ...u, is_banned: false };
          if (action === "verify") return { ...u, is_verified: true };
          if (action === "unverify") return { ...u, is_verified: false };
          return u;
        })
      );
      return;
    }
    try {
      const res = await authedFetch(`/admin/users/${userId}/${action}`, { method: "POST" });
      if (!res.ok) throw new Error("Action failed");
      const updated = await res.json();
      setUsers((us) => us.map((u) => (u.id === userId ? updated : u)));
    } catch (e) {
      setError(e.message);
    }
  };

  const filteredDemo = demoMode
    ? users.filter((u) => {
        if (filter === "banned" && !u.is_banned) return false;
        if (filter === "unverified" && u.is_verified) return false;
        if (query && !u.username.includes(query) && !u.email.includes(query)) return false;
        return true;
      })
    : users;

  return (
    <div style={{ minHeight: "100vh", background: "#0E0B1A", fontFamily: "'Inter', sans-serif", color: "#F2EEFA", padding: "28px 20px 60px" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&display=swap');
        input, select, button { font-family: 'Inter', sans-serif; }
        .row-btn { background: none; border: 1px solid #2c2444; color: #F2EEFA; border-radius: 8px; padding: 6px 10px; font-size: 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; }
        .row-btn:hover { border-color: #F5C84C; }
      `}</style>

      <div style={{ maxWidth: 920, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <ShieldCheck size={22} color="#F5C84C" />
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 22, margin: 0 }}>Nova World Admin</h1>
        </div>
        <p style={{ color: "#8B85A0", fontSize: 13, marginTop: 4, marginBottom: 20 }}>
          {demoMode ? "Preview mode with sample data — paste an admin access token below to connect to your live API." : "Connected to live API."}
        </p>

        <div style={{ display: "flex", gap: 8, marginBottom: 22 }}>
          <input
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="Paste admin access token (from POST /auth/login on an admin account)"
            style={{ flex: 1, background: "#171227", border: "1px solid #241d38", borderRadius: 10, padding: "10px 14px", color: "#F2EEFA", fontSize: 13, outline: "none" }}
          />
          <button onClick={applyToken} className="row-btn" style={{ borderColor: "#F5C84C", color: "#F5C84C", padding: "0 16px" }}>
            Connect
          </button>
        </div>

        {error && <div style={{ background: "rgba(255,79,163,0.1)", color: "#FF4FA3", padding: "10px 14px", borderRadius: 10, fontSize: 13, marginBottom: 16 }}>{error}</div>}

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
          <StatCard icon={Users} label="total users" value={stats.total_users} />
          <StatCard icon={ShieldAlert} label="banned" value={stats.banned_users} />
          <StatCard icon={BadgeCheck} label="verified" value={stats.verified_users} />
          <StatCard icon={FileImage} label="total posts" value={stats.total_posts} />
        </div>

        <div style={{ display: "flex", gap: 10, marginBottom: 16, alignItems: "center" }}>
          <div style={{ position: "relative", flex: 1 }}>
            <Search size={15} color="#8B85A0" style={{ position: "absolute", left: 12, top: 11 }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadAll()}
              placeholder="Search username or email…"
              style={{ width: "100%", background: "#171227", border: "1px solid #241d38", borderRadius: 10, padding: "9px 12px 9px 34px", color: "#F2EEFA", fontSize: 13, outline: "none", boxSizing: "border-box" }}
            />
          </div>
          <div style={{ position: "relative" }}>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{ appearance: "none", background: "#171227", border: "1px solid #241d38", borderRadius: 10, padding: "9px 30px 9px 12px", color: "#F2EEFA", fontSize: 13, outline: "none" }}
            >
              <option value="all">All users</option>
              <option value="banned">Banned only</option>
              <option value="unverified">Unverified only</option>
            </select>
            <ChevronDown size={14} color="#8B85A0" style={{ position: "absolute", right: 10, top: 11, pointerEvents: "none" }} />
          </div>
        </div>

        <div style={{ background: "#171227", border: "1px solid #241d38", borderRadius: 14, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #241d38", textAlign: "left" }}>
                {["User", "Status", "Joined", "Actions"].map((h) => (
                  <th key={h} style={{ padding: "12px 16px", color: "#8B85A0", fontWeight: 500, fontSize: 12 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredDemo.map((u) => (
                <tr key={u.id} style={{ borderBottom: "1px solid #1c1730" }}>
                  <td style={{ padding: "12px 16px" }}>
                    <div style={{ fontWeight: 600 }}>{u.username}{u.is_admin && <span style={{ marginLeft: 6 }}><Badge tone="gold">admin</Badge></span>}</div>
                    <div style={{ color: "#8B85A0", fontSize: 12 }}>{u.email}</div>
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {u.is_banned ? <Badge tone="danger">banned</Badge> : <Badge tone="ok">active</Badge>}
                      {u.is_verified && <Badge tone="gold">verified</Badge>}
                    </div>
                  </td>
                  <td style={{ padding: "12px 16px", color: "#8B85A0" }}>{new Date(u.created_at).toLocaleDateString()}</td>
                  <td style={{ padding: "12px 16px" }}>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {u.is_banned ? (
                        <button className="row-btn" onClick={() => runAction(u.id, "unban")}><ShieldCheck size={13} /> Unban</button>
                      ) : (
                        <button className="row-btn" onClick={() => runAction(u.id, "ban")}><ShieldOff size={13} /> Ban</button>
                      )}
                      {u.is_verified ? (
                        <button className="row-btn" onClick={() => runAction(u.id, "unverify")}>Unverify</button>
                      ) : (
                        <button className="row-btn" onClick={() => runAction(u.id, "verify")}><BadgeCheck size={13} /> Verify</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {filteredDemo.length === 0 && (
                <tr><td colSpan={4} style={{ padding: 24, textAlign: "center", color: "#8B85A0" }}>No users match.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {loading && <div style={{ color: "#8B85A0", fontSize: 12, marginTop: 10 }}>Loading…</div>}
      </div>
    </div>
  );
}
