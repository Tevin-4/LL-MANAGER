from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from database import db
from models import League, LEAGUE_STATUSES
from utils.decorators import login_required, role_required
from utils.helpers import require_fields

leagues_bp = Blueprint("leagues", __name__, url_prefix="/api/leagues")


@leagues_bp.route("", methods=["GET"])
def list_leagues():
    status = request.args.get("status")
    query = League.query
    if status:
        if status not in LEAGUE_STATUSES:
            return jsonify({"error": f"status must be one of {list(LEAGUE_STATUSES)}"}), 400
        query = query.filter_by(status=status)
    leagues = query.order_by(League.season.desc(), League.name.asc()).all()
    return jsonify([l.to_dict() for l in leagues]), 200


@leagues_bp.route("/<int:league_id>", methods=["GET"])
def get_league(league_id):
    league = League.query.get(league_id)
    if not league:
        return jsonify({"error": "League not found"}), 404
    return jsonify(league.to_dict()), 200


@leagues_bp.route("", methods=["POST"])
@role_required("admin", "league_admin")
def create_league():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["name", "season"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    status = data.get("status", "active")
    if status not in LEAGUE_STATUSES:
        return jsonify({"error": f"status must be one of {list(LEAGUE_STATUSES)}"}), 400

    league = League(
        name=data["name"],
        season=data["season"],
        admin_id=int(get_jwt_identity()),
        status=status,
    )
    db.session.add(league)
    db.session.commit()
    return jsonify(league.to_dict()), 201


def _can_manage_league(league):
    claims = get_jwt()
    if claims.get("role") == "admin":
        return True
    return claims.get("role") == "league_admin" and league.admin_id == int(get_jwt_identity())


@leagues_bp.route("/<int:league_id>", methods=["PUT"])
@role_required("admin", "league_admin")
def update_league(league_id):
    league = League.query.get(league_id)
    if not league:
        return jsonify({"error": "League not found"}), 404
    if not _can_manage_league(league):
        return jsonify({"error": "You do not have permission to modify this league"}), 403

    data = request.get_json(silent=True) or {}
    if "status" in data and data["status"] not in LEAGUE_STATUSES:
        return jsonify({"error": f"status must be one of {list(LEAGUE_STATUSES)}"}), 400

    for field in ("name", "season", "status"):
        if field in data:
            setattr(league, field, data[field])

    db.session.commit()
    return jsonify(league.to_dict()), 200


@leagues_bp.route("/<int:league_id>", methods=["DELETE"])
@role_required("admin", "league_admin")
def delete_league(league_id):
    league = League.query.get(league_id)
    if not league:
        return jsonify({"error": "League not found"}), 404
    if not _can_manage_league(league):
        return jsonify({"error": "You do not have permission to delete this league"}), 403

    db.session.delete(league)
    db.session.commit()
    return jsonify({"message": "League deleted successfully"}), 200
