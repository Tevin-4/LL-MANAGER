from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

# Enum value sets, mirroring the MySQL ENUM columns in the provided schema.
USER_ROLES = ("admin", "league_admin", "coach", "player")
LEAGUE_STATUSES = ("active", "completed", "paused")
MATCH_STATUSES = ("scheduled", "ongoing", "completed", "cancelled")
GOAL_TYPES = ("regular", "penalty", "own_goal")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(*USER_ROLES, name="user_role"), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(
        db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now()
    )

    player_profile = db.relationship(
        "Player", backref="user", uselist=False, foreign_keys="Player.user_id"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    season = db.Column(db.Integer, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.Enum(*LEAGUE_STATUSES, name="league_status"), default="active")
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

    admin = db.relationship("User", foreign_keys=[admin_id])
    teams = db.relationship("Team", backref="league", lazy=True, cascade="all, delete-orphan")
    matches = db.relationship("Match", backref="league", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "season": self.season,
            "admin_id": self.admin_id,
            "admin_username": self.admin.username if self.admin else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    city = db.Column(db.String(100))
    founded_year = db.Column(db.Integer)
    logo_url = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(
        db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now()
    )

    __table_args__ = (
        db.UniqueConstraint("name", "league_id", name="unique_team_league"),
    )

    coach = db.relationship("User", foreign_keys=[coach_id])
    players = db.relationship("Player", backref="team", lazy=True, cascade="all, delete-orphan")
    home_matches = db.relationship(
        "Match", foreign_keys="Match.home_team_id", backref="home_team", lazy=True
    )
    away_matches = db.relationship(
        "Match", foreign_keys="Match.away_team_id", backref="away_team", lazy=True
    )

    def to_dict(self, include_players=False):
        data = {
            "id": self.id,
            "name": self.name,
            "league_id": self.league_id,
            "league_name": self.league.name if self.league else None,
            "coach_id": self.coach_id,
            "coach_username": self.coach.username if self.coach else None,
            "city": self.city,
            "founded_year": self.founded_year,
            "logo_url": self.logo_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_players:
            data["players"] = [p.to_dict() for p in self.players]
        return data


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    jersey_number = db.Column(db.Integer, nullable=False)
    position = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    height_cm = db.Column(db.Integer)
    weight_kg = db.Column(db.Integer)
    nationality = db.Column(db.String(50))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(
        db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now()
    )

    __table_args__ = (
        db.UniqueConstraint("team_id", "jersey_number", name="unique_team_jersey"),
    )

    statistics = db.relationship(
        "PlayerStatistic", backref="player", lazy=True, cascade="all, delete-orphan"
    )
    goals = db.relationship("Goal", backref="player", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "jersey_number": self.jersey_number,
            "position": self.position,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "nationality": self.nationality,
        }


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False)
    stadium = db.Column(db.String(100))
    home_team_score = db.Column(db.Integer, default=0)
    away_team_score = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum(*MATCH_STATUSES, name="match_status"), default="scheduled")
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())
    updated_at = db.Column(
        db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now()
    )

    goals = db.relationship("Goal", backref="match", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "league_id": self.league_id,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "home_team_name": self.home_team.name if self.home_team else None,
            "away_team_name": self.away_team.name if self.away_team else None,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "stadium": self.stadium,
            "home_team_score": self.home_team_score,
            "away_team_score": self.away_team_score,
            "status": self.status,
        }


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    minute = db.Column(db.Integer, nullable=False)
    goal_type = db.Column(db.Enum(*GOAL_TYPES, name="goal_type"), default="regular")
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

    team = db.relationship("Team", foreign_keys=[team_id])

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "player_id": self.player_id,
            "player_name": self.player.user.username if self.player and self.player.user else None,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "minute": self.minute,
            "goal_type": self.goal_type,
        }


class PlayerStatistic(db.Model):
    __tablename__ = "player_statistics"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    matches_played = db.Column(db.Integer, default=0)
    goals_scored = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    updated_at = db.Column(
        db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now()
    )

    __table_args__ = (
        db.UniqueConstraint("player_id", "league_id", name="unique_player_league"),
    )

    league = db.relationship("League", foreign_keys=[league_id])

    def to_dict(self):
        return {
            "id": self.id,
            "player_id": self.player_id,
            "league_id": self.league_id,
            "matches_played": self.matches_played,
            "goals_scored": self.goals_scored,
            "assists": self.assists,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
        }


class Standing(db.Model):
    __tablename__ = "standings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    matches_played = db.Column(db.Integer, default=0)
    matches_won = db.Column(db.Integer, default=0)
    matches_drawn = db.Column(db.Integer, default=0)
    matches_lost = db.Column(db.Integer, default=0)
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    updated_at = db.Column(
        db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now()
    )

    __table_args__ = (
        db.UniqueConstraint("league_id", "team_id", name="unique_league_team"),
    )

    team = db.relationship("Team", foreign_keys=[team_id])

    def to_dict(self):
        return {
            "id": self.id,
            "league_id": self.league_id,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "matches_played": self.matches_played,
            "matches_won": self.matches_won,
            "matches_drawn": self.matches_drawn,
            "matches_lost": self.matches_lost,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "goal_difference": (self.goals_for or 0) - (self.goals_against or 0),
            "points": self.points,
        }
