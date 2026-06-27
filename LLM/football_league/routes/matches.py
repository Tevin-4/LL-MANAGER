from flask import Blueprint, request, jsonify
from database import db
from models import Match, Team, League, MATCH_STATUSES
from utils.decorators import role_required
from utils.helpers import require_fields, parse_datetime
from routes.standings import recalculate_league_standings

matches_bp = Blueprint("matches", __name__, url_prefix="/api/matches")

MANAGE_ROLES = ("admin", "league_admin", "coach")


@matches_bp.route("", methods=["GET"])
def list_matches():
    query = Match.query
    league_id = request.args.get("league_id", type=int)
    team_id = request.args.get("team_id", type=int)
    status = request.args.get("status")

    if league_id is not None:
        query = query.filter_by(league_id=league_id)
    if team_id is not None:
        query = query.filter(
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        )
    if status:
        if status not in MATCH_STATUSES:
            return jsonify({"error": f"status must be one of {list(MATCH_STATUSES)}"}), 400
        query = query.filter_by(status=status)

    matches = query.order_by(Match.match_date.asc()).all()
    return jsonify([m.to_dict() for m in matches]), 200


@matches_bp.route("/<int:match_id>", methods=["GET"])
def get_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404
    return jsonify(match.to_dict()), 200


@matches_bp.route("", methods=["POST"])
@role_required(*MANAGE_ROLES)
def create_match():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["league_id", "home_team_id", "away_team_id", "match_date"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if data["home_team_id"] == data["away_team_id"]:
        return jsonify({"error": "home_team_id and away_team_id must differ"}), 400

    if not League.query.get(data["league_id"]):
        return jsonify({"error": "League not found"}), 404
    home_team = Team.query.get(data["home_team_id"])
    away_team = Team.query.get(data["away_team_id"])
    if not home_team or not away_team:
        return jsonify({"error": "One or both teams not found"}), 404

    try:
        match_date = parse_datetime(data["match_date"])
    except ValueError:
        return jsonify(
            {"error": "match_date must be in ISO format, e.g. 2026-06-20T15:00:00"}
        ), 400

    status = data.get("status", "scheduled")
    if status not in MATCH_STATUSES:
        return jsonify({"error": f"status must be one of {list(MATCH_STATUSES)}"}), 400

    match = Match(
        league_id=data["league_id"],
        home_team_id=data["home_team_id"],
        away_team_id=data["away_team_id"],
        match_date=match_date,
        stadium=data.get("stadium"),
        home_team_score=data.get("home_team_score", 0),
        away_team_score=data.get("away_team_score", 0),
        status=status,
    )
    db.session.add(match)
    db.session.commit()

    if status == "completed":
        recalculate_league_standings(match.league_id)

    return jsonify(match.to_dict()), 201


@matches_bp.route("/<int:match_id>", methods=["PUT"])
@role_required(*MANAGE_ROLES)
def update_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    data = request.get_json(silent=True) or {}

    home_team_id = data.get("home_team_id", match.home_team_id)
    away_team_id = data.get("away_team_id", match.away_team_id)
    if home_team_id == away_team_id:
        return jsonify({"error": "home_team_id and away_team_id must differ"}), 400

    if "league_id" in data and not League.query.get(data["league_id"]):
        return jsonify({"error": "League not found"}), 404
    if "home_team_id" in data and not Team.query.get(data["home_team_id"]):
        return jsonify({"error": "Home team not found"}), 404
    if "away_team_id" in data and not Team.query.get(data["away_team_id"]):
        return jsonify({"error": "Away team not found"}), 404

    if "match_date" in data:
        try:
            data["match_date"] = parse_datetime(data["match_date"])
        except ValueError:
            return jsonify(
                {"error": "match_date must be in ISO format, e.g. 2026-06-20T15:00:00"}
            ), 400

    if "status" in data and data["status"] not in MATCH_STATUSES:
        return jsonify({"error": f"status must be one of {list(MATCH_STATUSES)}"}), 400

    leagues_to_refresh = {match.league_id}

    for field in (
        "league_id",
        "home_team_id",
        "away_team_id",
        "match_date",
        "stadium",
        "home_team_score",
        "away_team_score",
        "status",
    ):
        if field in data:
            setattr(match, field, data[field])

    leagues_to_refresh.add(match.league_id)
    db.session.commit()

    # Recalculate standings for any league this match belongs to (now or previously),
    # since editing a completed match's score/status/league must keep the table accurate.
    for league_id in leagues_to_refresh:
        recalculate_league_standings(league_id)

    return jsonify(match.to_dict()), 200


@matches_bp.route("/<int:match_id>", methods=["DELETE"])
@role_required(*MANAGE_ROLES)
def delete_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    league_id = match.league_id
    db.session.delete(match)
    db.session.commit()

    recalculate_league_standings(league_id)

    return jsonify({"message": "Match deleted successfully"}), 200
