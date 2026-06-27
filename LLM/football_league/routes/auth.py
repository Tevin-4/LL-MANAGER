from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from database import db
from models import User, USER_ROLES
from utils.decorators import login_required
from utils.helpers import require_fields

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["username", "email", "password", "role"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if data["role"] not in USER_ROLES:
        return jsonify({"error": f"role must be one of {list(USER_ROLES)}"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(username=data["username"], email=data["email"], role=data["role"])
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    token = create_access_token(
        identity=str(user.id), additional_claims={"role": user.role}
    )
    return jsonify({"user": user.to_dict(), "access_token": token}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["username", "password"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    user = User.query.filter_by(username=data["username"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    token = create_access_token(
        identity=str(user.id), additional_claims={"role": user.role}
    )
    return jsonify({"user": user.to_dict(), "access_token": token}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@auth_bp.route("/users", methods=["GET"])
@login_required
def list_users():
    """Lightweight user lookup, used by admin forms to link players/coaches to accounts."""
    role = request.args.get("role")
    query = User.query
    if role:
        if role not in USER_ROLES:
            return jsonify({"error": f"role must be one of {list(USER_ROLES)}"}), 400
        query = query.filter_by(role=role)
    users = query.order_by(User.username.asc()).all()
    return jsonify([u.to_dict() for u in users]), 200
