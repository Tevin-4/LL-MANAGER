from flask import Blueprint, request, jsonify, current_app
from database import db
from models import Standing, Team, Match, League
from utils.decorators import role_required

standings_bp = Blueprint("standings", __name__, url_prefix="/api/standings")


def recalculate_league_standings(league_id):
    """Recompute and persist the standings table for a league from its completed matches.

    Called whenever a match in the league is created, updated, or deleted, so the
    `standings` table stays in sync rather than going stale.
    """
    points_win = current_app.config.get("POINTS_WIN", 3)
    points_draw = current_app.config.get("POINTS_DRAW", 1)
    points_loss = current_app.config.get("POINTS_LOSS", 0)

    teams = Team.query.filter_by(league_id=league_id).all()
    totals = {
        team.id: {
            "matches_played": 0,
            "matches_won": 0,
            "matches_drawn": 0,
            "matches_lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "points": 0,
        }
        for team in teams
    }

    completed_matches = Match.query.filter_by(league_id=league_id, status="completed").all()
    for match in completed_matches:
        home = totals.get(match.home_team_id)
        away = totals.get(match.away_team_id)
        if home is None or away is None:
            continue
        hs, as_ = match.home_team_score or 0, match.away_team_score or 0

        home["matches_played"] += 1
        away["matches_played"] += 1
        home["goals_for"] += hs
        home["goals_against"] += as_
        away["goals_for"] += as_
        away["goals_against"] += hs

        if hs > as_:
            home["matches_won"] += 1
            home["points"] += points_win
            away["matches_lost"] += 1
            away["points"] += points_loss
        elif hs < as_:
            away["matches_won"] += 1
            away["points"] += points_win
            home["matches_lost"] += 1
            home["points"] += points_loss
        else:
            home["matches_drawn"] += 1
            away["matches_drawn"] += 1
            home["points"] += points_draw
            away["points"] += points_draw

    for team_id, row in totals.items():
        standing = Standing.query.filter_by(league_id=league_id, team_id=team_id).first()
        if not standing:
            standing = Standing(league_id=league_id, team_id=team_id)
            db.session.add(standing)
        for field, value in row.items():
            setattr(standing, field, value)

    db.session.commit()


@standings_bp.route("", methods=["GET"])
def get_standings():
    league_id = request.args.get("league_id", type=int)
    if league_id is None:
        return jsonify({"error": "league_id query parameter is required"}), 400
    if not League.query.get(league_id):
        return jsonify({"error": "League not found"}), 404

    standings = (
        Standing.query.filter_by(league_id=league_id)
        .all()
    )
    ranked = sorted(
        standings,
        key=lambda s: (
            -s.points,
            -((s.goals_for or 0) - (s.goals_against or 0)),
            -(s.goals_for or 0),
            s.team.name if s.team else "",
        ),
    )
    result = []
    for idx, s in enumerate(ranked, start=1):
        row = s.to_dict()
        row["position"] = idx
        result.append(row)

    return jsonify(result), 200


@standings_bp.route("/recalculate", methods=["POST"])
@role_required("admin", "league_admin")
def recalculate_standings():
    league_id = request.args.get("league_id", type=int) or (request.get_json(silent=True) or {}).get(
        "league_id"
    )
    if not league_id:
        return jsonify({"error": "league_id is required"}), 400
    if not League.query.get(league_id):
        return jsonify({"error": "League not found"}), 404

    recalculate_league_standings(league_id)
    return jsonify({"message": "Standings recalculated"}), 200
