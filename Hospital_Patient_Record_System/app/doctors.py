from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Doctor
from app.auth_utils import admin_required

doctors_bp = Blueprint("doctors", __name__)


def doctor_data(doctor):
    return {
        "id": doctor.id,
        "name": doctor.name,
        "specialization": doctor.specialization
    }


@doctors_bp.route("/doctors", methods=["GET"])
@admin_required()
def get_doctors():
    doctors = Doctor.query.all()
    return jsonify([doctor_data(d) for d in doctors]), 200


@doctors_bp.route("/doctors", methods=["POST"])
@admin_required()
def create_doctor():
    data = request.get_json()

    if not data.get("name") or not data.get("specialization"):
        return jsonify({
            "error": "Name and specialization are required"
        }), 400

    doctor = Doctor(
        name=data["name"],
        specialization=data["specialization"]
    )

    db.session.add(doctor)
    db.session.commit()

    return jsonify({
        "message": "Doctor created successfully",
        "doctor": doctor_data(doctor)
    }), 201


@doctors_bp.route("/doctors/<int:doctor_id>", methods=["GET"])
@admin_required()
def get_doctor(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    return jsonify(doctor_data(doctor)), 200


@doctors_bp.route("/doctors/<int:doctor_id>", methods=["PUT"])
@admin_required()
def update_doctor(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    data = request.get_json()

    doctor.name = data.get("name", doctor.name)
    doctor.specialization = data.get(
        "specialization",
        doctor.specialization
    )

    db.session.commit()

    return jsonify({
        "message": "Doctor updated successfully"
    }), 200


@doctors_bp.route("/doctors/<int:doctor_id>", methods=["PATCH"])
@admin_required()
def patch_doctor(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    data = request.get_json()

    if "name" in data:
        doctor.name = data["name"]

    if "specialization" in data:
        doctor.specialization = data["specialization"]

    db.session.commit()

    return jsonify({
        "message": "Doctor partially updated successfully"
    }), 200


@doctors_bp.route("/doctors/<int:doctor_id>", methods=["DELETE"])
@admin_required()
def delete_doctor(doctor_id):
    doctor = db.session.get(Doctor, doctor_id)

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    db.session.delete(doctor)
    db.session.commit()

    return jsonify({
        "message": "Doctor deleted successfully"
    }), 200