/**
 * api.js - Centralized API communication layer for the Football League dashboard.
 */
const API = (() => {
  const BASE_URL = "http://localhost:5000/api";

  function getToken() {
    return window.__AUTH_TOKEN__ || null;
  }

  function setToken(token) {
    window.__AUTH_TOKEN__ = token;
  }

  function clearToken() {
    window.__AUTH_TOKEN__ = null;
  }

  async function request(path, { method = "GET", body = null, auth = false } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const token = getToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }

    let response;
    try {
      response = await fetch(`${BASE_URL}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null,
      });
    } catch (err) {
      throw new Error("Network error: unable to reach the server.");
    }

    let data = null;
    try {
      data = await response.json();
    } catch (err) {
      data = null;
    }

    if (!response.ok) {
      const message = (data && data.error) || `Request failed with status ${response.status}`;
      throw new Error(message);
    }

    return data;
  }

  function qs(params = {}) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    );
    const s = new URLSearchParams(clean).toString();
    return s ? `?${s}` : "";
  }

  return {
    setToken,
    clearToken,
    getToken,

    // Auth
    register: (payload) => request("/auth/register", { method: "POST", body: payload }),
    login: (payload) => request("/auth/login", { method: "POST", body: payload }),
    me: () => request("/auth/me", { auth: true }),
    getUsers: (params = {}) => request(`/auth/users${qs(params)}`, { auth: true }),

    // Leagues
    getLeagues: (params = {}) => request(`/leagues${qs(params)}`),
    getLeague: (id) => request(`/leagues/${id}`),
    createLeague: (payload) => request("/leagues", { method: "POST", body: payload, auth: true }),
    updateLeague: (id, payload) => request(`/leagues/${id}`, { method: "PUT", body: payload, auth: true }),
    deleteLeague: (id) => request(`/leagues/${id}`, { method: "DELETE", auth: true }),

    // Teams
    getTeams: (params = {}) => request(`/teams${qs(params)}`),
    getTeam: (id) => request(`/teams/${id}`),
    createTeam: (payload) => request("/teams", { method: "POST", body: payload, auth: true }),
    updateTeam: (id, payload) => request(`/teams/${id}`, { method: "PUT", body: payload, auth: true }),
    deleteTeam: (id) => request(`/teams/${id}`, { method: "DELETE", auth: true }),

    // Players
    getPlayers: (params = {}) => request(`/players${qs(params)}`),
    getPlayer: (id) => request(`/players/${id}`),
    createPlayer: (payload) => request("/players", { method: "POST", body: payload, auth: true }),
    updatePlayer: (id, payload) => request(`/players/${id}`, { method: "PUT", body: payload, auth: true }),
    deletePlayer: (id) => request(`/players/${id}`, { method: "DELETE", auth: true }),
    getPlayerStatistics: (id, params = {}) => request(`/players/${id}/statistics${qs(params)}`),
    upsertPlayerStatistics: (id, payload) =>
      request(`/players/${id}/statistics`, { method: "PUT", body: payload, auth: true }),

    // Matches
    getMatches: (params = {}) => request(`/matches${qs(params)}`),
    getMatch: (id) => request(`/matches/${id}`),
    createMatch: (payload) => request("/matches", { method: "POST", body: payload, auth: true }),
    updateMatch: (id, payload) => request(`/matches/${id}`, { method: "PUT", body: payload, auth: true }),
    deleteMatch: (id) => request(`/matches/${id}`, { method: "DELETE", auth: true }),

    // Goals
    getGoals: (params = {}) => request(`/goals${qs(params)}`),
    createGoal: (payload) => request("/goals", { method: "POST", body: payload, auth: true }),
    deleteGoal: (id) => request(`/goals/${id}`, { method: "DELETE", auth: true }),

    // Standings
    getStandings: (leagueId) => request(`/standings${qs({ league_id: leagueId })}`),
    recalculateStandings: (leagueId) =>
      request(`/standings/recalculate${qs({ league_id: leagueId })}`, { method: "POST", auth: true }),
  };
})();
