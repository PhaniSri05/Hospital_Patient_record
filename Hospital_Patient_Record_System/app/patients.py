from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Patient
from app.auth_utils import admin_required

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/patients", methods=["GET"])
@admin_required()
def get_patients():
    patients = Patient.query.all()

    return jsonify([
        {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "contact": patient.contact
        }
        for patient in patients
    ]), 200


@patients_bp.route("/patients", methods=["POST"])
@admin_required()
def create_patient():
    data = request.get_json()

    required_fields = ["name", "age", "gender", "contact"]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    if Patient.query.filter_by(contact=data["contact"]).first():
        return jsonify({
            "error": "Patient with this contact already exists"
        }), 409

    patient = Patient(
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        contact=data["contact"]
    )

    db.session.add(patient)
    db.session.commit()

    return jsonify({
        "message": "Patient created successfully",
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "contact": patient.contact
        }
    }), 201

@patients_bp.route("/patients/<int:patient_id>", methods=["GET"])
@admin_required()
def get_patient(patient_id):
    patient = db.session.get(Patient, patient_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    return jsonify({
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "contact": patient.contact
    }), 200


@patients_bp.route("/patients/<int:patient_id>", methods=["PUT"])
@admin_required()
def update_patient(patient_id):
    patient = db.session.get(Patient, patient_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data = request.get_json()

    patient.name = data.get("name", patient.name)
    patient.age = data.get("age", patient.age)
    patient.gender = data.get("gender", patient.gender)
    patient.contact = data.get("contact", patient.contact)

    db.session.commit()

    return jsonify({
        "message": "Patient updated successfully"
    }), 200


@patients_bp.route("/patients/<int:patient_id>", methods=["PATCH"])
@admin_required()
def patch_patient(patient_id):
    patient = db.session.get(Patient, patient_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data = request.get_json()

    if "name" in data:
        patient.name = data["name"]

    if "age" in data:
        patient.age = data["age"]

    if "gender" in data:
        patient.gender = data["gender"]

    if "contact" in data:
        patient.contact = data["contact"]

    db.session.commit()

    return jsonify({
        "message": "Patient partially updated successfully"
    }), 200


@patients_bp.route("/patients/<int:patient_id>", methods=["DELETE"])
@admin_required()
def delete_patient(patient_id):
    patient = db.session.get(Patient, patient_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    db.session.delete(patient)
    db.session.commit()

    return jsonify({
        "message": "Patient deleted successfully"
    }), 200