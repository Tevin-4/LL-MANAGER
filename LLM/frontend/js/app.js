/**
 * app.js - Shared application bootstrap: auth state, league context, nav, helpers.
 */
const App = (() => {
  const SESSION_KEY = "fl_session";
  const LEAGUE_KEY = "fl_selected_league";

  const MANAGE_ROLES = ["admin", "league_admin", "coach"];
  const LEAGUE_OWNER_ROLES = ["admin", "league_admin"];

  function saveSession(user, token) {
    API.setToken(token);
    const payload = JSON.stringify({ user, token });
    window.__SESSION__ = payload;
    try {
      sessionStorage.setItem(SESSION_KEY, payload);
    } catch (err) {
      // sessionStorage may be unavailable (private browsing); memory-only fallback.
    }
  }

  function loadSession() {
    let raw = window.__SESSION__ || null;
    if (!raw) {
      try {
        raw = sessionStorage.getItem(SESSION_KEY);
      } catch (err) {
        raw = null;
      }
    }
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw);
      API.setToken(parsed.token);
      return parsed;
    } catch (err) {
      return null;
    }
  }

  function clearSession() {
    API.clearToken();
    window.__SESSION__ = null;
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch (err) {
      // ignore
    }
  }

  function isLoggedIn() {
    const session = loadSession();
    return !!(session && session.token);
  }

  function currentRole() {
    const session = loadSession();
    return session && session.user ? session.user.role : null;
  }

  function hasRole(...roles) {
    const role = currentRole();
    return !!role && roles.includes(role);
  }

  function canManage() {
    return hasRole(...MANAGE_ROLES);
  }

  function canManageLeagues() {
    return hasRole(...LEAGUE_OWNER_ROLES);
  }

  // --- League context (shared across teams/players/matches/standings pages) ---

  function getSelectedLeagueId() {
    let id = window.__SELECTED_LEAGUE__;
    if (!id) {
      try {
        id = sessionStorage.getItem(LEAGUE_KEY);
      } catch (err) {
        id = null;
      }
    }
    return id ? parseInt(id, 10) : null;
  }

  function setSelectedLeagueId(id) {
    window.__SELECTED_LEAGUE__ = id;
    try {
      if (id) sessionStorage.setItem(LEAGUE_KEY, id);
      else sessionStorage.removeItem(LEAGUE_KEY);
    } catch (err) {
      // ignore
    }
    document.dispatchEvent(new CustomEvent("league-changed", { detail: { leagueId: id } }));
  }

  async function populateLeagueSelectors() {
    const selectors = document.querySelectorAll("[data-league-select]");
    if (selectors.length === 0) return;

    let leagues = [];
    try {
      leagues = await API.getLeagues();
    } catch (err) {
      return;
    }

    const current = getSelectedLeagueId();
    const validIds = leagues.map((l) => l.id);
    const fallback = validIds.includes(current) ? current : leagues[0]?.id || null;
    if (fallback !== current) setSelectedLeagueId(fallback);

    selectors.forEach((select) => {
      select.innerHTML = leagues
        .map((l) => `<option value="${l.id}">${escapeHtml(l.name)} (${l.season})</option>`)
        .join("");
      if (fallback) select.value = fallback;
      select.addEventListener("change", () => {
        setSelectedLeagueId(parseInt(select.value, 10));
      });
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str ?? "";
    return div.innerHTML;
  }

  function showError(container, message) {
    if (!container) return;
    container.textContent = message;
    container.classList.add("visible");
    setTimeout(() => container.classList.remove("visible"), 5000);
  }

  function showSuccess(container, message) {
    if (!container) return;
    container.textContent = message;
    container.classList.add("visible", "success");
    setTimeout(() => container.classList.remove("visible", "success"), 4000);
  }

  function formatDate(isoString) {
    if (!isoString) return "TBD";
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return isoString;
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function highlightActiveNav() {
    const current = window.location.pathname.split("/").pop() || "index.html";
    
    // Desktop navigation
    document.querySelectorAll("nav a[data-page]").forEach((link) => {
      if (link.getAttribute("data-page") === current) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    // Mobile tab bar
    document.querySelectorAll(".mobile-tab-item[data-page]").forEach((link) => {
      if (link.getAttribute("data-page") === current) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });
  }

  function toggleRoleBasedControls() {
    const loggedIn = isLoggedIn();
    document.querySelectorAll("[data-manage-only]").forEach((el) => {
      el.style.display = canManage() ? "" : "none";
    });
    document.querySelectorAll("[data-league-admin-only]").forEach((el) => {
      el.style.display = canManageLeagues() ? "" : "none";
    });

    const loginLink = document.querySelector("[data-nav-login]");
    const logoutBtn = document.querySelector("[data-nav-logout]");
    const userBadge = document.querySelector("[data-nav-user]");
    if (loginLink) loginLink.style.display = loggedIn ? "none" : "";
    if (logoutBtn) logoutBtn.style.display = loggedIn ? "" : "none";
    if (userBadge) {
      const session = loadSession();
      userBadge.textContent = loggedIn ? `${session.user.username} (${session.user.role})` : "";
    }

    // Update mobile avatar
    updateMobileAvatar();
  }

  function updateMobileAvatar() {
    const avatarIcon = document.querySelector(".mobile-avatar-icon");
    if (!avatarIcon) return;

    const session = loadSession();
    if (session && session.user) {
      const initials = session.user.username.substring(0, 2).toUpperCase();
      avatarIcon.textContent = initials;
      avatarIcon.title = session.user.username;
    }
  }

  function setupMobileNavigation() {
    // Avatar menu toggle
    const avatarMenu = document.querySelector(".mobile-avatar-menu");
    const bottomSheet = document.querySelector(".mobile-bottom-sheet");
    const overlay = document.querySelector(".mobile-overlay");
    const closeBtn = document.querySelector(".mobile-bottom-sheet-close");

    if (!avatarMenu || !bottomSheet || !overlay) return;

    function openMenu() {
      bottomSheet.classList.add("active");
      overlay.classList.add("active");
    }

    function closeMenu() {
      bottomSheet.classList.remove("active");
      overlay.classList.remove("active");
    }

    avatarMenu.addEventListener("click", openMenu);
    closeBtn?.addEventListener("click", closeMenu);
    overlay.addEventListener("click", closeMenu);

    // Close menu when clicking menu items
    document.querySelectorAll(".mobile-bottom-sheet-item").forEach((item) => {
      item.addEventListener("click", closeMenu);
    });

    // Tab bar navigation
    document.querySelectorAll(".mobile-tab-item[data-href]").forEach((tab) => {
      tab.addEventListener("click", (e) => {
        e.preventDefault();
        window.location.href = tab.getAttribute("data-href");
      });
    });
  }

  function bindLogout() {
    const logoutBtn = document.querySelector("[data-nav-logout]");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        clearSession();
        const depth = window.location.pathname.includes("/pages/") ? "../" : "";
        window.location.href = `${depth}index.html`;
      });
    }

    // Mobile logout button
    const mobileLogoutBtn = document.querySelector(".mobile-logout-btn");
    if (mobileLogoutBtn) {
      mobileLogoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        clearSession();
        const depth = window.location.pathname.includes("/pages/") ? "../" : "";
        window.location.href = `${depth}index.html`;
      });
    }
  }

  function init() {
    loadSession();
    highlightActiveNav();
    toggleRoleBasedControls();
    bindLogout();
    populateLeagueSelectors();
    setupMobileNavigation();
  }

  document.addEventListener("DOMContentLoaded", init);

  return {
    saveSession,
    loadSession,
    clearSession,
    isLoggedIn,
    currentRole,
    hasRole,
    canManage,
    canManageLeagues,
    getSelectedLeagueId,
    setSelectedLeagueId,
    showError,
    showSuccess,
    formatDate,
    escapeHtml,
  };
})();
