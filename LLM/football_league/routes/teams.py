from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from database import db
from models import Team, League, User
from utils.decorators import role_required
from utils.helpers import require_fields

teams_bp = Blueprint("teams", __name__, url_prefix="/api/teams")

MANAGE_ROLES = ("admin", "league_admin", "coach")


@teams_bp.route("", methods=["GET"])
def list_teams():
    query = Team.query
    league_id = request.args.get("league_id", type=int)
    if league_id is not None:
        query = query.filter_by(league_id=league_id)
    teams = query.order_by(Team.name.asc()).all()
    return jsonify([t.to_dict() for t in teams]), 200


@teams_bp.route("/<int:team_id>", methods=["GET"])
def get_team(team_id):
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404
    return jsonify(team.to_dict(include_players=True)), 200


@teams_bp.route("", methods=["POST"])
@role_required(*MANAGE_ROLES)
def create_team():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["name", "league_id"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not League.query.get(data["league_id"]):
        return jsonify({"error": "League not found"}), 404

    if data.get("coach_id") and not User.query.get(data["coach_id"]):
        return jsonify({"error": "Coach (user) not found"}), 404

    team = Team(
        name=data["name"],
        league_id=data["league_id"],
        coach_id=data.get("coach_id"),
        city=data.get("city"),
        founded_year=data.get("founded_year"),
        logo_url=data.get("logo_url"),
    )
    db.session.add(team)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A team with that name already exists in this league"}), 409

    return jsonify(team.to_dict()), 201


@teams_bp.route("/<int:team_id>", methods=["PUT"])
@role_required(*MANAGE_ROLES)
def update_team(team_id):
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404

    data = request.get_json(silent=True) or {}

    if "league_id" in data and not League.query.get(data["league_id"]):
        return jsonify({"error": "League not found"}), 404
    if "coach_id" in data and data["coach_id"] and not User.query.get(data["coach_id"]):
        return jsonify({"error": "Coach (user) not found"}), 404

    for field in ("name", "league_id", "coach_id", "city", "founded_year", "logo_url"):
        if field in data:
            setattr(team, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A team with that name already exists in this league"}), 409

    return jsonify(team.to_dict()), 200


@teams_bp.route("/<int:team_id>", methods=["DELETE"])
@role_required(*MANAGE_ROLES)
def delete_team(team_id):
    team = Team.query.get(team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404

    db.session.delete(team)
    db.session.commit()
    return jsonify({"message": "Team deleted successfully"}), 200
