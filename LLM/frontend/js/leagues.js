/**
 * leagues.js - Render and manage the Leagues page.
 */
const LeaguesPage = (() => {
  let leagues = [];

  async function loadLeagues() {
    const listEl = document.getElementById("leagues-list");
    const errorEl = document.getElementById("leagues-error");
    if (!listEl) return;

    listEl.innerHTML = `<p class="loading">Loading leagues...</p>`;
    try {
      leagues = await API.getLeagues();
      renderLeagues();
    } catch (err) {
      App.showError(errorEl, err.message);
      listEl.innerHTML = `<p class="empty-state">Could not load leagues.</p>`;
    }
  }

  function renderLeagues() {
    const listEl = document.getElementById("leagues-list");
    if (!listEl) return;

    if (leagues.length === 0) {
      listEl.innerHTML = `<p class="empty-state">No leagues yet. Create one to get started.</p>`;
      return;
    }

    listEl.innerHTML = leagues
      .map(
        (l) => `
        <div class="card" data-league-id="${l.id}">
          <div class="card-header">
            <h3>${App.escapeHtml(l.name)} <span class="status-badge status-${l.status}">${l.status}</span></h3>
            <div class="card-actions" data-league-admin-only style="display:none;">
              <button data-action="edit" data-id="${l.id}">Edit</button>
              <button data-action="delete" data-id="${l.id}">Delete</button>
            </div>
          </div>
          <p>Season: ${l.season}</p>
          <p>Admin: ${App.escapeHtml(l.admin_username || "—")}</p>
        </div>
      `
      )
      .join("");

    if (App.canManageLeagues()) {
      document.querySelectorAll("[data-league-admin-only]").forEach((el) => (el.style.display = ""));
    }

    listEl.querySelectorAll('[data-action="edit"]').forEach((btn) =>
      btn.addEventListener("click", () => openEditForm(parseInt(btn.dataset.id, 10)))
    );
    listEl.querySelectorAll('[data-action="delete"]').forEach((btn) =>
      btn.addEventListener("click", () => deleteLeague(parseInt(btn.dataset.id, 10)))
    );
  }

  function openEditForm(id) {
    const league = leagues.find((l) => l.id === id);
    if (!league) return;
    const form = document.getElementById("league-form");
    if (!form) return;
    form.elements["league_id"].value = league.id;
    form.elements["name"].value = league.name;
    form.elements["season"].value = league.season;
    form.elements["status"].value = league.status;
    document.getElementById("league-form-title").textContent = "Edit League";
  }

  function resetForm() {
    const form = document.getElementById("league-form");
    if (!form) return;
    form.reset();
    form.elements["league_id"].value = "";
    document.getElementById("league-form-title").textContent = "Create League";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const errorEl = document.getElementById("leagues-error");
    const successEl = document.getElementById("leagues-success");

    const id = form.elements["league_id"].value;
    const payload = {
      name: form.elements["name"].value.trim(),
      season: parseInt(form.elements["season"].value, 10),
      status: form.elements["status"].value || "active",
    };

    if (!payload.name || !payload.season) {
      App.showError(errorEl, "League name and season are required.");
      return;
    }

    try {
      if (id) {
        await API.updateLeague(parseInt(id, 10), payload);
        App.showSuccess(successEl, "League updated successfully.");
      } else {
        await API.createLeague(payload);
        App.showSuccess(successEl, "League created successfully.");
      }
      resetForm();
      await loadLeagues();
      await App.setSelectedLeagueId(null); // force selector refresh on next page load
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  async function deleteLeague(id) {
    if (!confirm("Delete this league? This removes its teams, players, matches and standings.")) return;
    const errorEl = document.getElementById("leagues-error");
    try {
      await API.deleteLeague(id);
      await loadLeagues();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  function init() {
    if (!document.getElementById("leagues-list")) return;
    loadLeagues();
    const form = document.getElementById("league-form");
    if (form) form.addEventListener("submit", handleSubmit);
    const cancelBtn = document.getElementById("league-form-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", resetForm);
  }

  document.addEventListener("DOMContentLoaded", init);

  return { loadLeagues };
})();
