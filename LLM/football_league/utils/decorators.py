from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models import User


def login_required(fn):
    """Require a valid JWT to access the route."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """Require a valid JWT belonging to a user with role 'admin'."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Admin privileges required"}), 403
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles):
    """Require a valid JWT belonging to a user whose role is in `roles`."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify(
                    {"error": f"Requires one of the following roles: {', '.join(roles)}"}
                ), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user():
    """Fetch the User object for the current JWT identity, or None."""
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    return User.query.get(int(user_id))


def get_current_role():
    """Fetch the role claim from the current JWT, or None."""
    try:
        claims = get_jwt()
    except Exception:
        return None
    return claims.get("role")
