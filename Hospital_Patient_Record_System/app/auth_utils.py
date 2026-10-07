from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def admin_required():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            claims = get_jwt()

            if claims.get("role") != "admin":
                return jsonify({
                    "error": "Admin access required"
                }), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator


def doctor_or_admin_required():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()

            claims = get_jwt()
            role = claims.get("role")

            if role not in ["admin", "doctor"]:
                return jsonify({
                    "error": "Doctor or admin access required"
                }), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator