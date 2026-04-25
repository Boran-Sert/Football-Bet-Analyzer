const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Backend API'ye istek atan yardimci fonksiyon.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = { "Content-Type": "application/json", ...options.headers };

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Auth
  register: (data) => request("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => request("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) }),
  forgotPassword: (data) => request("/api/v1/auth/forgot-password", { method: "POST", body: JSON.stringify(data) }),
  resetPassword: (data) => request("/api/v1/auth/reset-password", { method: "POST", body: JSON.stringify(data) }),
  getMe: () => request("/api/v1/auth/me"),

  // Matches
  getMatches: ({ league, season, status } = {}) => {
    const params = new URLSearchParams();
    if (league) params.set("league", league);
    if (season) params.set("season", season);
    if (status) params.set("status", status);
    const qs = params.toString();
    return request(`/api/v1/matches${qs ? `?${qs}` : ""}`);
  },

  // Analysis
  analyze: (matchId, topN = 5) => request(`/api/v1/analysis/${matchId}?top_n=${topN}`),
};
