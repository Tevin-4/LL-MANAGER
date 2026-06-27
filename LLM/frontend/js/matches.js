/**
 * matches.js - Render and manage the Matches page (scoped to the selected league).
 */
const MatchesPage = (() => {
  let matches = [];
  let teams = [];
  let players = [];
  let openGoalsMatchId = null;

  async function loadData() {
    const listEl = document.getElementById("matches-list");
    const errorEl = document.getElementById("matches-error");
    if (!listEl) return;

    const leagueId = App.getSelectedLeagueId();
    if (!leagueId) {
      listEl.innerHTML = `<p class="empty-state">Create a league first, then come back here.</p>`;
      return;
    }

    listEl.innerHTML = `<p class="loading">Loading matches...</p>`;
    try {
      [matches, teams, players] = await Promise.all([
        API.getMatches({ league_id: leagueId }),
        API.getTeams({ league_id: leagueId }),
        API.getPlayers({ league_id: leagueId }),
      ]);
      populateTeamSelects();
      renderMatches();
    } catch (err) {
      App.showError(errorEl, err.message);
      listEl.innerHTML = `<p class="empty-state">Could not load matches.</p>`;
    }
  }

  function populateTeamSelects() {
    const options =
      `<option value="">Select team</option>` +
      teams.map((t) => `<option value="${t.id}">${App.escapeHtml(t.name)}</option>`).join("");
    const homeSelect = document.querySelector('#match-form select[name="home_team_id"]');
    const awaySelect = document.querySelector('#match-form select[name="away_team_id"]');
    if (homeSelect) homeSelect.innerHTML = options;
    if (awaySelect) awaySelect.innerHTML = options;
  }

  function renderMatches() {
    const listEl = document.getElementById("matches-list");
    if (!listEl) return;

    if (matches.length === 0) {
      listEl.innerHTML = `<p class="empty-state">No matches scheduled yet in this league.</p>`;
      return;
    }

    listEl.innerHTML = matches
      .map(
        (m) => `
        <div class="card match-card" data-match-id="${m.id}">
          <div class="match-teams">
            <span>${App.escapeHtml(m.home_team_name)}</span>
            <span class="score">${
              m.status === "completed" || m.status === "ongoing"
                ? `${m.home_team_score} - ${m.away_team_score}`
                : "vs"
            }</span>
            <span>${App.escapeHtml(m.away_team_name)}</span>
          </div>
          <div class="match-meta">
            <span>${App.formatDate(m.match_date)}</span>
            <span class="status-badge status-${m.status}">${m.status.replace("_", " ")}</span>
            ${m.stadium ? `<span>${App.escapeHtml(m.stadium)}</span>` : ""}
          </div>
          <div class="card-actions">
            <button data-action="goals" data-id="${m.id}"><img id="goal-net" src="../goal-net.ico"> Goals</button>
            <span data-manage-only style="display:none;">
              <button data-action="edit" data-id="${m.id}">Edit</button>
              <button data-action="delete" data-id="${m.id}">Delete</button>
            </span>
          </div>
          <div class="goals-panel" id="goals-panel-${m.id}" style="display:none;"></div>
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
      btn.addEventListener("click", () => deleteMatch(parseInt(btn.dataset.id, 10)))
    );
    listEl.querySelectorAll('[data-action="goals"]').forEach((btn) =>
      btn.addEventListener("click", () => toggleGoalsPanel(parseInt(btn.dataset.id, 10)))
    );
  }

  async function toggleGoalsPanel(matchId) {
    const panel = document.getElementById(`goals-panel-${matchId}`);
    if (!panel) return;

    if (openGoalsMatchId === matchId) {
      panel.style.display = "none";
      openGoalsMatchId = null;
      return;
    }
    openGoalsMatchId = matchId;

    panel.style.display = "block";
    panel.innerHTML = `<p class="loading">Loading goals...</p>`;

    try {
      const goals = await API.getGoals({ match_id: matchId });
      const match = matches.find((m) => m.id === matchId);
      const eligiblePlayers = players.filter(
        (p) => p.team_id === match.home_team_id || p.team_id === match.away_team_id
      );

      panel.innerHTML = `
        <ul class="goals-list">
          ${
            goals.length
              ? goals
                  .map(
                    (g) => `
              <li>${g.minute}' — ${App.escapeHtml(g.player_name || "Unknown")} (${App.escapeHtml(
                      g.team_name
                    )}) <span class="status-badge">${g.goal_type.replace("_", " ")}</span>
                ${
                  App.canManage()
                    ? `<button data-goal-delete="${g.id}" class="btn-delete">×</button>`
                    : ""
                }
              </li>`
                  )
                  .join("")
              : `<li class="empty-state">No goals recorded yet.</li>`
          }
        </ul>
        ${
          App.canManage()
            ? `
          <form class="entity-form goal-form" data-match-id="${matchId}">
            <div class="form-row">
              <div>
                <label>Scorer</label>
                <select name="player_id" required>
                  <option value="">Select player</option>
                  ${eligiblePlayers
                    .map(
                      (p) =>
                        `<option value="${p.id}" data-team="${p.team_id}">${App.escapeHtml(
                          p.username
                        )} (${App.escapeHtml(p.team_name)})</option>`
                    )
                    .join("")}
                </select>
              </div>
              <div>
                <label>Minute</label>
                <input type="number" name="minute" min="0" max="130" required />
              </div>
              <div>
                <label>Type</label>
                <select name="goal_type">
                  <option value="regular">Regular</option>
                  <option value="penalty">Penalty</option>
                  <option value="own_goal">Own Goal</option>
                </select>
              </div>
            </div>
            <button type="submit">Add Goal</button>
          </form>`
            : ""
        }
      `;

      panel.querySelectorAll("[data-goal-delete]").forEach((btn) =>
        btn.addEventListener("click", async () => {
          try {
            await API.deleteGoal(parseInt(btn.dataset.goalDelete, 10));
            toggleGoalsPanel(matchId);
            toggleGoalsPanel(matchId);
          } catch (err) {
            App.showError(document.getElementById("matches-error"), err.message);
          }
        })
      );

      const goalForm = panel.querySelector(".goal-form");
      if (goalForm) {
        goalForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          const playerSelect = goalForm.elements["player_id"];
          const teamId = parseInt(playerSelect.selectedOptions[0]?.dataset.team, 10);
          try {
            await API.createGoal({
              match_id: matchId,
              player_id: parseInt(playerSelect.value, 10),
              team_id: teamId,
              minute: parseInt(goalForm.elements["minute"].value, 10),
              goal_type: goalForm.elements["goal_type"].value,
            });
            openGoalsMatchId = null;
            toggleGoalsPanel(matchId);
          } catch (err) {
            App.showError(document.getElementById("matches-error"), err.message);
          }
        });
      }
    } catch (err) {
      panel.innerHTML = `<p class="empty-state">Could not load goals.</p>`;
    }
  }

  function openEditForm(id) {
    const match = matches.find((m) => m.id === id);
    if (!match) return;
    const form = document.getElementById("match-form");
    if (!form) return;
    form.elements["match_id"].value = match.id;
    form.elements["home_team_id"].value = match.home_team_id;
    form.elements["away_team_id"].value = match.away_team_id;
    form.elements["match_date"].value = match.match_date ? match.match_date.slice(0, 16) : "";
    form.elements["stadium"].value = match.stadium || "";
    form.elements["status"].value = match.status;
    form.elements["home_team_score"].value = match.home_team_score ?? 0;
    form.elements["away_team_score"].value = match.away_team_score ?? 0;
    document.getElementById("match-form-title").textContent = "Edit Match";
  }

  function resetForm() {
    const form = document.getElementById("match-form");
    if (!form) return;
    form.reset();
    form.elements["match_id"].value = "";
    document.getElementById("match-form-title").textContent = "Schedule Match";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const errorEl = document.getElementById("matches-error");
    const successEl = document.getElementById("matches-success");
    const leagueId = App.getSelectedLeagueId();

    const id = form.elements["match_id"].value;
    const homeId = form.elements["home_team_id"].value;
    const awayId = form.elements["away_team_id"].value;

    if (!leagueId || !homeId || !awayId || !form.elements["match_date"].value) {
      App.showError(errorEl, "League, home team, away team, and match date are required.");
      return;
    }
    if (homeId === awayId) {
      App.showError(errorEl, "Home and away teams must be different.");
      return;
    }

    const payload = {
      league_id: leagueId,
      home_team_id: parseInt(homeId, 10),
      away_team_id: parseInt(awayId, 10),
      match_date: form.elements["match_date"].value,
      stadium: form.elements["stadium"].value.trim() || null,
      status: form.elements["status"].value,
      home_team_score: form.elements["home_team_score"].value
        ? parseInt(form.elements["home_team_score"].value, 10)
        : 0,
      away_team_score: form.elements["away_team_score"].value
        ? parseInt(form.elements["away_team_score"].value, 10)
        : 0,
    };

    try {
      if (id) {
        await API.updateMatch(parseInt(id, 10), payload);
        App.showSuccess(successEl, "Match updated successfully.");
      } else {
        await API.createMatch(payload);
        App.showSuccess(successEl, "Match scheduled successfully.");
      }
      resetForm();
      await loadData();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  async function deleteMatch(id) {
    if (!confirm("Delete this match?")) return;
    const errorEl = document.getElementById("matches-error");
    try {
      await API.deleteMatch(id);
      await loadData();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  function init() {
    if (!document.getElementById("matches-list")) return;
    loadData();
    document.addEventListener("league-changed", loadData);
    const form = document.getElementById("match-form");
    if (form) form.addEventListener("submit", handleSubmit);
    const cancelBtn = document.getElementById("match-form-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", resetForm);
  }

  document.addEventListener("DOMContentLoaded", init);

  return { loadData };
})();
