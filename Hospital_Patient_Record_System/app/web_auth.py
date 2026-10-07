from functools import wraps

from flask import session, redirect, url_for, flash

from app.models import User


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login to continue.")
            return redirect(url_for("web.login"))

        return func(*args, **kwargs)

    return wrapper


def admin_web_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login to continue.")
            return redirect(url_for("web.login"))

        if session.get("role") != "admin":
            flash("Admin access required.")
            return redirect(url_for("web.dashboard"))

        return func(*args, **kwargs)

    return wrapper


def doctor_or_admin_web_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login to continue.")
            return redirect(url_for("web.login"))

        if session.get("role") not in ["admin", "doctor"]:
            flash("Access denied.")
            return redirect(url_for("web.dashboard"))

        return func(*args, **kwargs)

    return wrapper


def get_logged_in_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.query.get(user_id)