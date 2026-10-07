from flask import Flask
from config import Config
from app.extensions import db, jwt


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    from app import models

    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api")

    from app.patients import patients_bp
    app.register_blueprint(patients_bp, url_prefix="/api")

    from app.doctors import doctors_bp
    app.register_blueprint(doctors_bp, url_prefix="/api")

    from app.appointments import appointments_bp
    app.register_blueprint(
        appointments_bp,
        url_prefix="/api"
    )

    from app.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix="/api")

    from app.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix="/api")

    from app.web import web_bp
    app.register_blueprint(web_bp)

    return app