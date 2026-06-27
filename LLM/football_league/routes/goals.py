from flask import Blueprint, request, jsonify
from database import db
from models import Goal, Match, Player, Team, PlayerStatistic, GOAL_TYPES
from utils.decorators import role_required
from utils.helpers import require_fields

goals_bp = Blueprint("goals", __name__, url_prefix="/api/goals")

MANAGE_ROLES = ("admin", "league_admin", "coach")


@goals_bp.route("", methods=["GET"])
def list_goals():
    query = Goal.query
    match_id = request.args.get("match_id", type=int)
    player_id = request.args.get("player_id", type=int)
    if match_id is not None:
        query = query.filter_by(match_id=match_id)
    if player_id is not None:
        query = query.filter_by(player_id=player_id)

    goals = query.order_by(Goal.minute.asc()).all()
    return jsonify([g.to_dict() for g in goals]), 200


@goals_bp.route("", methods=["POST"])
@role_required(*MANAGE_ROLES)
def create_goal():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["match_id", "player_id", "team_id", "minute"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    match = Match.query.get(data["match_id"])
    if not match:
        return jsonify({"error": "Match not found"}), 404
    if not Player.query.get(data["player_id"]):
        return jsonify({"error": "Player not found"}), 404
    if not Team.query.get(data["team_id"]):
        return jsonify({"error": "Team not found"}), 404
    if data["team_id"] not in (match.home_team_id, match.away_team_id):
        return jsonify({"error": "team_id must be one of the two teams playing this match"}), 400

    goal_type = data.get("goal_type", "regular")
    if goal_type not in GOAL_TYPES:
        return jsonify({"error": f"goal_type must be one of {list(GOAL_TYPES)}"}), 400

    goal = Goal(
        match_id=data["match_id"],
        player_id=data["player_id"],
        team_id=data["team_id"],
        minute=data["minute"],
        goal_type=goal_type,
    )
    db.session.add(goal)

    # Keep the scoring player's per-league goal tally in sync (own goals don't count for the scorer).
    if goal_type != "own_goal":
        stats = PlayerStatistic.query.filter_by(
            player_id=data["player_id"], league_id=match.league_id
        ).first()
        if not stats:
            stats = PlayerStatistic(player_id=data["player_id"], league_id=match.league_id)
            db.session.add(stats)
        stats.goals_scored = (stats.goals_scored or 0) + 1

    db.session.commit()
    return jsonify(goal.to_dict()), 201


@goals_bp.route("/<int:goal_id>", methods=["DELETE"])
@role_required(*MANAGE_ROLES)
def delete_goal(goal_id):
    goal = Goal.query.get(goal_id)
    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    if goal.goal_type != "own_goal":
        match = Match.query.get(goal.match_id)
        stats = PlayerStatistic.query.filter_by(
            player_id=goal.player_id, league_id=match.league_id
        ).first()
        if stats and stats.goals_scored:
            stats.goals_scored -= 1

    db.session.delete(goal)
    db.session.commit()
    return jsonify({"message": "Goal deleted successfully"}), 200
