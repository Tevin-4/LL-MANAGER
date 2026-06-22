/**
 * players.js - Render and manage the Players page (scoped to the selected league).
 */
const PlayersPage = (() => {
  let players = [];
  let teams = [];
  let playerUsers = [];

  async function loadData() {
    const listEl = document.getElementById("players-list");
    const errorEl = document.getElementById("players-error");
    if (!listEl) return;

    const leagueId = App.getSelectedLeagueId();
    if (!leagueId) {
      listEl.innerHTML = `<p class="empty-state">Create a league first, then come back here.</p>`;
      return;
    }

    listEl.innerHTML = `<p class="loading">Loading players...</p>`;
    try {
      [players, teams, playerUsers] = await Promise.all([
        API.getPlayers({ league_id: leagueId }),
        API.getTeams({ league_id: leagueId }),
        API.getUsers({ role: "player" }).catch(() => []),
      ]);
      populateTeamFilter();
      populateFormSelects();
      renderPlayers();
    } catch (err) {
      App.showError(errorEl, err.message);
      listEl.innerHTML = `<p class="empty-state">Could not load players.</p>`;
    }
  }

  function populateTeamFilter() {
    const filter = document.getElementById("players-team-filter");
    if (!filter) return;
    filter.innerHTML =
      `<option value="">All Teams</option>` +
      teams.map((t) => `<option value="${t.id}">${App.escapeHtml(t.name)}</option>`).join("");
  }

  function populateFormSelects() {
    const teamSelect = document.querySelector('#player-form select[name="team_id"]');
    if (teamSelect) {
      teamSelect.innerHTML =
        `<option value="">Select team</option>` +
        teams.map((t) => `<option value="${t.id}">${App.escapeHtml(t.name)}</option>`).join("");
    }
    const userSelect = document.querySelector('#player-form select[name="user_id"]');
    if (userSelect) {
      userSelect.innerHTML =
        `<option value="">Select player account</option>` +
        playerUsers.map((u) => `<option value="${u.id}">${App.escapeHtml(u.username)}</option>`).join("");
    }
  }

  function renderPlayers() {
    const listEl = document.getElementById("players-list");
    if (!listEl) return;

    if (players.length === 0) {
      listEl.innerHTML = `<p class="empty-state">No players found in this league.</p>`;
      return;
    }

    listEl.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>#</th><th>Username</th><th>Position</th><th>Team</th><th>Nationality</th><th>Ht/Wt</th>
            <th data-manage-only style="display:none;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${players
            .map(
              (p) => `
            <tr data-player-id="${p.id}">
              <td>${p.jersey_number ?? "—"}</td>
              <td>${App.escapeHtml(p.username || "—")}</td>
              <td>${App.escapeHtml(p.position || "—")}</td>
              <td>${App.escapeHtml(p.team_name || "—")}</td>
              <td>${App.escapeHtml(p.nationality || "—")}</td>
              <td>${p.height_cm ? `${p.height_cm}cm` : "—"} / ${p.weight_kg ? `${p.weight_kg}kg` : "—"}</td>
              <td data-manage-only style="display:none;">
                <button data-action="edit" data-id="${p.id}">Edit</button>
                <button data-action="delete" data-id="${p.id}">Delete</button>
              </td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;

    if (App.canManage()) {
      document.querySelectorAll("[data-manage-only]").forEach((el) => (el.style.display = ""));
    }

    listEl.querySelectorAll('[data-action="edit"]').forEach((btn) =>
      btn.addEventListener("click", () => openEditForm(parseInt(btn.dataset.id, 10)))
    );
    listEl.querySelectorAll('[data-action="delete"]').forEach((btn) =>
      btn.addEventListener("click", () => deletePlayer(parseInt(btn.dataset.id, 10)))
    );
  }

  function openEditForm(id) {
    const player = players.find((p) => p.id === id);
    if (!player) return;
    const form = document.getElementById("player-form");
    if (!form) return;
    form.elements["player_id"].value = player.id;
    form.elements["user_id"].value = player.user_id;
    form.elements["position"].value = player.position || "";
    form.elements["jersey_number"].value = player.jersey_number ?? "";
    form.elements["date_of_birth"].value = player.date_of_birth || "";
    form.elements["nationality"].value = player.nationality || "";
    form.elements["height_cm"].value = player.height_cm ?? "";
    form.elements["weight_kg"].value = player.weight_kg ?? "";
    form.elements["team_id"].value = player.team_id;
    document.getElementById("player-form-title").textContent = "Edit Player";
  }

  function resetForm() {
    const form = document.getElementById("player-form");
    if (!form) return;
    form.reset();
    form.elements["player_id"].value = "";
    document.getElementById("player-form-title").textContent = "Add Player";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const errorEl = document.getElementById("players-error");
    const successEl = document.getElementById("players-success");

    const id = form.elements["player_id"].value;
    const payload = {
      user_id: form.elements["user_id"].value ? parseInt(form.elements["user_id"].value, 10) : null,
      position: form.elements["position"].value || null,
      jersey_number: form.elements["jersey_number"].value
        ? parseInt(form.elements["jersey_number"].value, 10)
        : null,
      date_of_birth: form.elements["date_of_birth"].value || null,
      nationality: form.elements["nationality"].value.trim() || null,
      height_cm: form.elements["height_cm"].value ? parseInt(form.elements["height_cm"].value, 10) : null,
      weight_kg: form.elements["weight_kg"].value ? parseInt(form.elements["weight_kg"].value, 10) : null,
      team_id: form.elements["team_id"].value ? parseInt(form.elements["team_id"].value, 10) : null,
    };

    if (!payload.user_id || !payload.team_id || !payload.jersey_number) {
      App.showError(errorEl, "Player account, team, and jersey number are required.");
      return;
    }

    try {
      if (id) {
        await API.updatePlayer(parseInt(id, 10), payload);
        App.showSuccess(successEl, "Player updated successfully.");
      } else {
        await API.createPlayer(payload);
        App.showSuccess(successEl, "Player created successfully.");
      }
      resetForm();
      await loadData();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  async function deletePlayer(id) {
    if (!confirm("Delete this player?")) return;
    const errorEl = document.getElementById("players-error");
    try {
      await API.deletePlayer(id);
      await loadData();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  function handleFilterChange() {
    const filter = document.getElementById("players-team-filter");
    if (!filter) return;
    filter.addEventListener("change", async () => {
      const teamId = filter.value;
      const leagueId = App.getSelectedLeagueId();
      try {
        players = await API.getPlayers(teamId ? { team_id: teamId } : { league_id: leagueId });
        renderPlayers();
      } catch (err) {
        App.showError(document.getElementById("players-error"), err.message);
      }
    });
  }

  function init() {
    if (!document.getElementById("players-list")) return;
    loadData();
    document.addEventListener("league-changed", loadData);
    const form = document.getElementById("player-form");
    if (form) form.addEventListener("submit", handleSubmit);
    const cancelBtn = document.getElementById("player-form-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", resetForm);
    handleFilterChange();
  }

  document.addEventListener("DOMContentLoaded", init);

  return { loadData };
})();
