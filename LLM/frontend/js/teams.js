/**
 * teams.js - Render and manage the Teams page (scoped to the selected league).
 */
const TeamsPage = (() => {
  let teams = [];
  let coaches = [];

  async function loadTeams() {
    const listEl = document.getElementById("teams-list");
    const errorEl = document.getElementById("teams-error");
    if (!listEl) return;

    const leagueId = App.getSelectedLeagueId();
    if (!leagueId) {
      listEl.innerHTML = `<p class="empty-state">Create a league first, then come back here.</p>`;
      return;
    }

    listEl.innerHTML = `<p class="loading">Loading teams...</p>`;
    try {
      [teams, coaches] = await Promise.all([
        API.getTeams({ league_id: leagueId }),
        API.getUsers({ role: "coach" }).catch(() => []),
      ]);
      populateCoachSelect();
      renderTeams();
    } catch (err) {
      App.showError(errorEl, err.message);
      listEl.innerHTML = `<p class="empty-state">Could not load teams.</p>`;
    }
  }

  function populateCoachSelect() {
    const select = document.querySelector('#team-form select[name="coach_id"]');
    if (!select) return;
    select.innerHTML =
      `<option value="">No coach assigned</option>` +
      coaches.map((c) => `<option value="${c.id}">${App.escapeHtml(c.username)}</option>`).join("");
  }

  function renderTeams() {
    const listEl = document.getElementById("teams-list");
    if (!listEl) return;

    if (teams.length === 0) {
      listEl.innerHTML = `<p class="empty-state">No teams yet in this league. Add one to get started.</p>`;
      return;
    }

    listEl.innerHTML = teams
      .map(
        (team) => `
        <div class="card" data-team-id="${team.id}">
          <div class="card-header">
            <h3>${App.escapeHtml(team.name)}</h3>
            <div class="card-actions" data-manage-only style="display:none;">
              <button data-action="edit" data-id="${team.id}">Edit</button>
              <button data-action="delete" data-id="${team.id}">Delete</button>
            </div>
          </div>
          <p>City: ${App.escapeHtml(team.city || "—")}</p>
          <p>Founded: ${team.founded_year || "—"}</p>
          <p>Coach: ${App.escapeHtml(team.coach_username || "—")}</p>
        </div>
      `
      )
      .join("");

    if (App.canManage()) {
      document.querySelectorAll("[data-manage-only]").forEach((el) => (el.style.display = ""));
    }

    listEl.querySelectorAll('[data-action="edit"]').forEach((btn) =>
      btn.addEventListener("click", () => openEditForm(parseInt(btn.dataset.id, 10)))
    );
    listEl.querySelectorAll('[data-action="delete"]').forEach((btn) =>
      btn.addEventListener("click", () => deleteTeam(parseInt(btn.dataset.id, 10)))
    );
  }

  function openEditForm(id) {
    const team = teams.find((t) => t.id === id);
    if (!team) return;
    const form = document.getElementById("team-form");
    if (!form) return;
    form.elements["team_id"].value = team.id;
    form.elements["name"].value = team.name;
    form.elements["city"].value = team.city || "";
    form.elements["founded_year"].value = team.founded_year || "";
    form.elements["logo_url"].value = team.logo_url || "";
    form.elements["coach_id"].value = team.coach_id || "";
    document.getElementById("team-form-title").textContent = "Edit Team";
  }

  function resetForm() {
    const form = document.getElementById("team-form");
    if (!form) return;
    form.reset();
    form.elements["team_id"].value = "";
    document.getElementById("team-form-title").textContent = "Add Team";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const errorEl = document.getElementById("teams-error");
    const successEl = document.getElementById("teams-success");
    const leagueId = App.getSelectedLeagueId();

    if (!leagueId) {
      App.showError(errorEl, "Select a league first.");
      return;
    }

    const id = form.elements["team_id"].value;
    const payload = {
      name: form.elements["name"].value.trim(),
      league_id: leagueId,
      city: form.elements["city"].value.trim() || null,
      founded_year: form.elements["founded_year"].value
        ? parseInt(form.elements["founded_year"].value, 10)
        : null,
      logo_url: form.elements["logo_url"].value.trim() || null,
      coach_id: form.elements["coach_id"].value ? parseInt(form.elements["coach_id"].value, 10) : null,
    };

    if (!payload.name) {
      App.showError(errorEl, "Team name is required.");
      return;
    }

    try {
      if (id) {
        await API.updateTeam(parseInt(id, 10), payload);
        App.showSuccess(successEl, "Team updated successfully.");
      } else {
        await API.createTeam(payload);
        App.showSuccess(successEl, "Team created successfully.");
      }
      resetForm();
      await loadTeams();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  async function deleteTeam(id) {
    if (!confirm("Delete this team? This will also remove its players.")) return;
    const errorEl = document.getElementById("teams-error");
    try {
      await API.deleteTeam(id);
      await loadTeams();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  function init() {
    if (!document.getElementById("teams-list")) return;
    loadTeams();
    document.addEventListener("league-changed", loadTeams);
    const form = document.getElementById("team-form");
    if (form) form.addEventListener("submit", handleSubmit);
    const cancelBtn = document.getElementById("team-form-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", resetForm);
  }

  document.addEventListener("DOMContentLoaded", init);

  return { loadTeams };
})();
