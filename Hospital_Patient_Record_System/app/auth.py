from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "role": user.role
    }), 200