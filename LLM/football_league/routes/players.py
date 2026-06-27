from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from database import db
from models import Player, Team, User, PlayerStatistic, League
from utils.decorators import role_required
from utils.helpers import require_fields, parse_date

players_bp = Blueprint("players", __name__, url_prefix="/api/players")

MANAGE_ROLES = ("admin", "league_admin", "coach")


@players_bp.route("", methods=["GET"])
def list_players():
    query = Player.query
    team_id = request.args.get("team_id", type=int)
    if team_id is not None:
        query = query.filter_by(team_id=team_id)
    league_id = request.args.get("league_id", type=int)
    if league_id is not None:
        query = query.join(Team).filter(Team.league_id == league_id)

    players = query.all()
    return jsonify([p.to_dict() for p in players]), 200


@players_bp.route("/<int:player_id>", methods=["GET"])
def get_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    return jsonify(player.to_dict()), 200


@players_bp.route("", methods=["POST"])
@role_required(*MANAGE_ROLES)
def create_player():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["user_id", "team_id", "jersey_number"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not User.query.get(data["user_id"]):
        return jsonify({"error": "User not found"}), 404
    if not Team.query.get(data["team_id"]):
        return jsonify({"error": "Team not found"}), 404

    try:
        dob = parse_date(data.get("date_of_birth"))
    except ValueError:
        return jsonify({"error": "date_of_birth must be in YYYY-MM-DD format"}), 400

    player = Player(
        user_id=data["user_id"],
        team_id=data["team_id"],
        jersey_number=data["jersey_number"],
        position=data.get("position"),
        date_of_birth=dob,
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        nationality=data.get("nationality"),
    )
    db.session.add(player)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "That jersey number is already taken on this team"}), 409

    return jsonify(player.to_dict()), 201


@players_bp.route("/<int:player_id>", methods=["PUT"])
@role_required(*MANAGE_ROLES)
def update_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json(silent=True) or {}

    if "team_id" in data and not Team.query.get(data["team_id"]):
        return jsonify({"error": "Team not found"}), 404
    if "user_id" in data and not User.query.get(data["user_id"]):
        return jsonify({"error": "User not found"}), 404

    if "date_of_birth" in data:
        try:
            data["date_of_birth"] = parse_date(data["date_of_birth"])
        except ValueError:
            return jsonify({"error": "date_of_birth must be in YYYY-MM-DD format"}), 400

    for field in (
        "user_id",
        "team_id",
        "jersey_number",
        "position",
        "date_of_birth",
        "height_cm",
        "weight_kg",
        "nationality",
    ):
        if field in data:
            setattr(player, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "That jersey number is already taken on this team"}), 409

    return jsonify(player.to_dict()), 200


@players_bp.route("/<int:player_id>", methods=["DELETE"])
@role_required(*MANAGE_ROLES)
def delete_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    db.session.delete(player)
    db.session.commit()
    return jsonify({"message": "Player deleted successfully"}), 200


# --- Player statistics (per league) -----------------------------------------

@players_bp.route("/<int:player_id>/statistics", methods=["GET"])
def get_player_statistics(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    league_id = request.args.get("league_id", type=int)
    query = PlayerStatistic.query.filter_by(player_id=player_id)
    if league_id is not None:
        query = query.filter_by(league_id=league_id)

    stats = query.all()
    return jsonify([s.to_dict() for s in stats]), 200


@players_bp.route("/<int:player_id>/statistics", methods=["PUT"])
@role_required(*MANAGE_ROLES)
def upsert_player_statistics(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["league_id"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not League.query.get(data["league_id"]):
        return jsonify({"error": "League not found"}), 404

    stats = PlayerStatistic.query.filter_by(
        player_id=player_id, league_id=data["league_id"]
    ).first()
    if not stats:
        stats = PlayerStatistic(player_id=player_id, league_id=data["league_id"])
        db.session.add(stats)

    for field in ("matches_played", "goals_scored", "assists", "yellow_cards", "red_cards"):
        if field in data:
            setattr(stats, field, data[field])

    db.session.commit()
    return jsonify(stats.to_dict()), 200
