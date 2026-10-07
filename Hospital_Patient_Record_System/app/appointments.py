from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

from app.extensions import db
from app.models import Appointment, Patient, Doctor, User


appointments_bp = Blueprint("appointments", __name__)


def appointment_data(appointment):
    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "date": appointment.date.isoformat(),
        "diagnosis": appointment.diagnosis,
        "status": appointment.status,
        "recovery_date": (
            appointment.recovery_date.isoformat()
            if appointment.recovery_date
            else None
        )
    }


def get_current_user():
    verify_jwt_in_request()

    claims = get_jwt()

    user_id = int(claims.get("sub"))
    role = claims.get("role")

    user = db.session.get(User, user_id)

    return user, role


def can_access_appointment(appointment, user, role):
    if role == "admin":
        return True

    if role == "doctor":
        return (
            user is not None
            and user.doctor_id == appointment.doctor_id
        )

    return False


# ---------------------------------------------------------
# GET ALL APPOINTMENTS
# Admin: Can see all appointments
# Doctor: Can see only their own appointments
# ---------------------------------------------------------

@appointments_bp.route("/appointments", methods=["GET"])
def get_appointments():

    user, role = get_current_user()

    doctor_id = request.args.get("doctor_id", type=int)

    if role == "admin":

        if doctor_id:
            appointments = Appointment.query.filter_by(
                doctor_id=doctor_id
            ).all()
        else:
            appointments = Appointment.query.all()

    elif role == "doctor":

        if not user or not user.doctor_id:
            return jsonify({
                "error": "Doctor account is not linked to a doctor"
            }), 403

        # Doctor can only see their own appointments
        if doctor_id and doctor_id != user.doctor_id:
            return jsonify({
                "error": "Doctors can only view their own appointments"
            }), 403

        appointments = Appointment.query.filter_by(
            doctor_id=user.doctor_id
        ).all()

    else:

        return jsonify({
            "error": "Access denied"
        }), 403

    return jsonify([
        appointment_data(a)
        for a in appointments
    ]), 200


# ---------------------------------------------------------
# CREATE APPOINTMENT
# Admin only
# ---------------------------------------------------------

@appointments_bp.route("/appointments", methods=["POST"])
def create_appointment():
    user, role = get_current_user()

    if role != "admin":
        return jsonify({
            "error": "Only admin can create appointments"
        }), 403

    data = request.get_json() or {}

    required_fields = [
        "patient_id",
        "doctor_id",
        "date",
        "diagnosis"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    patient = db.session.get(
        Patient,
        data["patient_id"]
    )

    doctor = db.session.get(
        Doctor,
        data["doctor_id"]
    )

    if not patient:
        return jsonify({
            "error": "Patient not found"
        }), 404

    if not doctor:
        return jsonify({
            "error": "Doctor not found"
        }), 404

    try:
        appointment_date = datetime.strptime(
            data["date"],
            "%Y-%m-%d"
        ).date()

        recovery_date = None

        if data.get("recovery_date"):
            recovery_date = datetime.strptime(
                data["recovery_date"],
                "%Y-%m-%d"
            ).date()

    except ValueError:
        return jsonify({
            "error": "Date must be in YYYY-MM-DD format"
        }), 400

    appointment = Appointment(
        patient_id=data["patient_id"],
        doctor_id=data["doctor_id"],
        date=appointment_date,
        diagnosis=data["diagnosis"],
        status=data.get(
            "status",
            "Under Treatment"
        ),
        recovery_date=recovery_date
    )

    db.session.add(appointment)
    db.session.commit()

    return jsonify({
        "message": "Appointment created successfully",
        "appointment": appointment_data(appointment)
    }), 201


# ---------------------------------------------------------
# GET APPOINTMENT BY ID
# Admin: Any appointment
# Doctor: Only own appointment
# ---------------------------------------------------------

@appointments_bp.route(
    "/appointments/<int:appointment_id>",
    methods=["GET"]
)
def get_appointment(appointment_id):
    user, role = get_current_user()

    appointment = db.session.get(
        Appointment,
        appointment_id
    )

    if not appointment:
        return jsonify({
            "error": "Appointment not found"
        }), 404

    if not can_access_appointment(
        appointment,
        user,
        role
    ):
        return jsonify({
            "error": "Access denied"
        }), 403

    return jsonify(
        appointment_data(appointment)
    ), 200


# ---------------------------------------------------------
# UPDATE APPOINTMENT
# Admin: Any appointment
# Doctor: Only own appointment
# ---------------------------------------------------------

@appointments_bp.route(
    "/appointments/<int:appointment_id>",
    methods=["PUT"]
)
def update_appointment(appointment_id):
    user, role = get_current_user()

    appointment = db.session.get(
        Appointment,
        appointment_id
    )

    if not appointment:
        return jsonify({
            "error": "Appointment not found"
        }), 404

    if not can_access_appointment(
        appointment,
        user,
        role
    ):
        return jsonify({
            "error": "You can only edit your own appointments"
        }), 403

    data = request.get_json() or {}

    # Admin can change patient
    if "patient_id" in data:

        if role != "admin":
            return jsonify({
                "error": "Doctors cannot change the patient"
            }), 403

        patient = db.session.get(
            Patient,
            data["patient_id"]
        )

        if not patient:
            return jsonify({
                "error": "Patient not found"
            }), 404

        appointment.patient_id = data["patient_id"]

    # Admin can change doctor
    if "doctor_id" in data:

        if role != "admin":
            return jsonify({
                "error": "Doctors cannot change the doctor"
            }), 403

        doctor = db.session.get(
            Doctor,
            data["doctor_id"]
        )

        if not doctor:
            return jsonify({
                "error": "Doctor not found"
            }), 404

        appointment.doctor_id = data["doctor_id"]

    # Update date
    if "date" in data:
        try:
            appointment.date = datetime.strptime(
                data["date"],
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return jsonify({
                "error": "Date must be in YYYY-MM-DD format"
            }), 400

    # Update diagnosis
    if "diagnosis" in data:
        appointment.diagnosis = data["diagnosis"]

    # Update status
    if "status" in data:
        allowed_statuses = [
            "Recovered",
            "Under Treatment",
            "Critical"
        ]

        if data["status"] not in allowed_statuses:
            return jsonify({
                "error": "Invalid status"
            }), 400

        appointment.status = data["status"]

    # Update recovery date
    if "recovery_date" in data:

        if data["recovery_date"]:
            try:
                appointment.recovery_date = datetime.strptime(
                    data["recovery_date"],
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                return jsonify({
                    "error": "Recovery date must be YYYY-MM-DD"
                }), 400

        else:
            appointment.recovery_date = None

    db.session.commit()

    return jsonify({
        "message": "Appointment updated successfully",
        "appointment": appointment_data(appointment)
    }), 200


# ---------------------------------------------------------
# DELETE APPOINTMENT
# Admin only
# ---------------------------------------------------------

@appointments_bp.route(
    "/appointments/<int:appointment_id>",
    methods=["DELETE"]
)
def delete_appointment(appointment_id):
    user, role = get_current_user()

    if role != "admin":
        return jsonify({
            "error": "Only admin can delete appointments"
        }), 403

    appointment = db.session.get(
        Appointment,
        appointment_id
    )

    if not appointment:
        return jsonify({
            "error": "Appointment not found"
        }), 404

    db.session.delete(appointment)
    db.session.commit()

    return jsonify({
        "message": "Appointment deleted successfully"
    }), 200