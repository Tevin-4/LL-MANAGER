import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import config
from database import db, init_db


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 1. Initialize structural base extensions first
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))
    JWTManager(app)

    # 2. Import Blueprints AND their corresponding models into memory FIRST
    from routes.auth import auth_bp
    from routes.leagues import leagues_bp
    from routes.teams import teams_bp
    from routes.players import players_bp
    from routes.matches import matches_bp
    from routes.goals import goals_bp
    from routes.standings import standings_bp

    # 3. Register Blueprints so Flask maps out routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(leagues_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(players_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(standings_bp)

    # 4. NOW initialize database table creation.
    # Moving this to the bottom ensures all tables (like teams) are loaded 
    # into SQLAlchemy's registry before create_all() is called!
    init_db(app)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True), host="0.0.0.0", port=5000)
