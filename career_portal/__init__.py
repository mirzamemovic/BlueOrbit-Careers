from pathlib import Path

from flask import Flask
from flask_jwt_extended import JWTManager

from .api import create_api_blueprint
from .db import init_app as init_db_app
from .db import initialize_database
from .views import web_bp


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="blueorbit-dev-key",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{Path(app.instance_path) / 'blueorbit.sqlite3'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY="blueorbit-jwt-dev-key-for-course-assignment",
        JSON_SORT_KEYS=False,
    )

    if test_config:
        app.config.update(test_config)

    if app.config.get("DATABASE"):
        database_path = Path(app.config["DATABASE"])
        if not database_path.is_absolute():
            database_path = Path(app.root_path).parent / database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    init_db_app(app)
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def missing_token(reason):
        return {"error": "Authorization required.", "details": reason}, 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return {"error": "Invalid token.", "details": reason}, 401

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return {"error": "Token has expired."}, 401

    with app.app_context():
        initialize_database(seed=not app.config.get("TESTING", False))

    app.register_blueprint(web_bp)
    app.register_blueprint(create_api_blueprint("api"))
    app.register_blueprint(create_api_blueprint("prefixed_api"), url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "app": "BlueOrbit Careers"}

    return app
