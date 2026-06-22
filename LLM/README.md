# Football League Manager

A full-stack football (soccer) league management system: a Flask + SQLAlchemy REST API backend over **MySQL**, and a vanilla HTML/CSS/JS frontend. The schema matches `database_schema.sql` exactly.

## Project Structure

```
football_league/        # Backend (Flask)
├── app.py               # App factory + entry point
├── config.py            # Config (dev/prod/testing) — MySQL via PyMySQL
├── database.py          # SQLAlchemy init
├── models.py            # User, League, Team, Player, Match, Goal, PlayerStatistic, Standing
├── routes/               # Blueprints: auth, leagues, teams, players, matches, goals, standings
└── utils/                 # Role-based auth decorators + helpers

frontend/                # Frontend (static, no build step)
├── index.html            # Landing/login/register page
├── css/                  # style.css + responsive.css
├── js/                    # api.js, app.js, leagues.js, teams.js, players.js, matches.js, standings.js
└── pages/                 # leagues, dashboard, teams, players, matches, standings

database_schema.sql      # Exact MySQL schema this backend targets
```

## Database Setup

```bash
mysql -u root -p < database_schema.sql
```

## Backend Setup

```bash
cd football_league
pip install -r requirements.txt
export DB_USER=root DB_PASSWORD=yourpassword DB_HOST=localhost DB_NAME=football_league
python app.py
```

The API runs at `http://localhost:5000`.

### Roles

The schema's `users.role` enum drives access control everywhere:

| Role | Can do |
|---|---|
| `admin` | Everything |
| `league_admin` | Create/manage their own leagues, teams, players, matches within them |
| `coach` | Manage teams/players/matches/goals (not leagues) |
| `player` | Read-only — browses teams, players, matches, standings |

Register with `{"role": "..."}` to pick one.

### Key endpoints

| Method | Endpoint | Auth |
|---|---|---|
| POST | /api/auth/register, /api/auth/login | none |
| GET | /api/auth/me | JWT |
| GET | /api/auth/users?role= | JWT (used to link coaches/players to accounts) |
| GET | /api/leagues | none |
| POST/PUT/DELETE | /api/leagues... | admin / league_admin (owner) |
| GET | /api/teams?league_id= | none |
| POST/PUT/DELETE | /api/teams... | admin / league_admin / coach |
| GET | /api/players?league_id=&team_id= | none |
| POST/PUT/DELETE | /api/players... | admin / league_admin / coach |
| GET/PUT | /api/players/\<id\>/statistics | GET: none, PUT: admin/league_admin/coach |
| GET | /api/matches?league_id=&team_id=&status= | none |
| POST/PUT/DELETE | /api/matches... | admin / league_admin / coach |
| GET/POST/DELETE | /api/goals | GET: none, write: admin/league_admin/coach |
| GET | /api/standings?league_id= | none |
| POST | /api/standings/recalculate?league_id= | admin / league_admin |

## Frontend Setup

```bash
cd frontend
python3 -m http.server 8080
```

Open `http://localhost:8080`. Edit `BASE_URL` in `js/api.js` if the API runs elsewhere.

The nav bar includes a **league selector** — almost everything (teams, players, matches, standings) is scoped to whichever league is currently selected, matching the schema's league-centric design. Create a league first (Leagues page) before adding teams.

## Notable design decisions / fixes from the raw schema

- **Standings are a real, persisted table** (matching `standings` in the schema) rather than computed on the fly. `routes/standings.py` recalculates and upserts it automatically whenever a match is created, updated, or deleted in that league — so it can never drift out of sync, while still matching the schema's "updated after each match" comment.
- **Players are linked to `users`**, not given their own name fields — a player's display name comes from their user account, matching `players.user_id`. The frontend's player form picks an existing `role=player` account rather than typing a name.
- **Teams are scoped to a `league_id`** and optionally a `coach_id` (a `role=coach` user) — the frontend always sends the currently-selected league when creating a team, team, match, etc.
- **Goals are first-class events**: recording one auto-increments the scorer's `player_statistics.goals_scored` for that league (own goals don't credit the scorer), keeping the two tables consistent without manual bookkeeping.
- **Role-based access**: write endpoints require `admin`, `league_admin`, or `coach` (leagues themselves require `admin`/`league_admin`); `player` accounts and anonymous visitors get read-only access — verified with an automated end-to-end test that a `player`-role token is rejected (403) on a team-creation attempt.
- Match status enum is exactly `scheduled/ongoing/completed/cancelled` per the schema (no extra "postponed" status was added).
- Validation added for: duplicate team names per league, duplicate jersey numbers per team, identical home/away teams, goal `team_id` must be one of the match's two teams, and malformed dates.
- Added `routes/__init__.py` / `utils/__init__.py` so those folders are valid Python packages (a common gap when writing this kind of file tree by hand).
