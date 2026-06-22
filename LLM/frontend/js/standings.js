/**
 * standings.js - Render the league Standings page/table (persisted standings table).
 */
const StandingsPage = (() => {
  async function loadStandings() {
    const container = document.getElementById("standings-table-container");
    const errorEl = document.getElementById("standings-error");
    if (!container) return;

    const leagueId = App.getSelectedLeagueId();
    if (!leagueId) {
      container.innerHTML = `<p class="empty-state">Create a league first, then come back here.</p>`;
      return;
    }

    container.innerHTML = `<p class="loading">Loading standings...</p>`;
    try {
      const standings = await API.getStandings(leagueId);
      renderStandings(standings);
    } catch (err) {
      App.showError(errorEl, err.message);
      container.innerHTML = `<p class="empty-state">Could not load standings.</p>`;
    }
  }

  function renderStandings(standings) {
    const container = document.getElementById("standings-table-container");
    if (!container) return;

    if (standings.length === 0) {
      container.innerHTML = `<p class="empty-state">No standings data available yet.</p>`;
      return;
    }

    container.innerHTML = `
      <table class="data-table standings-table">
        <thead>
          <tr>
            <th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th>
            <th>GF</th><th>GA</th><th>GD</th><th>Pts</th>
          </tr>
        </thead>
        <tbody>
          ${standings
            .map(
              (row) => `
            <tr>
              <td>${row.position}</td>
              <td class="team-name">${App.escapeHtml(row.team_name)}</td>
              <td>${row.matches_played}</td>
              <td>${row.matches_won}</td>
              <td>${row.matches_drawn}</td>
              <td>${row.matches_lost}</td>
              <td>${row.goals_for}</td>
              <td>${row.goals_against}</td>
              <td>${row.goal_difference > 0 ? "+" : ""}${row.goal_difference}</td>
              <td class="points">${row.points}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  async function handleRecalculate() {
    const leagueId = App.getSelectedLeagueId();
    const errorEl = document.getElementById("standings-error");
    if (!leagueId) return;
    try {
      await API.recalculateStandings(leagueId);
      await loadStandings();
    } catch (err) {
      App.showError(errorEl, err.message);
    }
  }

  function init() {
    if (!document.getElementById("standings-table-container")) return;
    loadStandings();
    document.addEventListener("league-changed", loadStandings);
    const btn = document.getElementById("standings-recalculate");
    if (btn) btn.addEventListener("click", handleRecalculate);
  }

  document.addEventListener("DOMContentLoaded", init);

  return { loadStandings };
})();
