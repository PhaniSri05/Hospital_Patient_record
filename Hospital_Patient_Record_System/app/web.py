from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from app.extensions import db
from app.models import Patient, Doctor, Appointment, User

from app.web_auth import (
    login_required,
    admin_web_required,
    doctor_or_admin_web_required,
    get_logged_in_user
)


web_bp = Blueprint("web", __name__)


# =========================================================
# LOGIN
# =========================================================

@web_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(
            username=username
        ).first()

        if not user or user.password != password:

            flash("Invalid username or password.")

            return render_template("login.html")

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        session["doctor_id"] = user.doctor_id

        flash("Login successful!")

        return redirect(url_for("web.dashboard"))

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@web_bp.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("web.login"))


# =========================================================
# DASHBOARD
# =========================================================

@web_bp.route("/")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        patient_count=Patient.query.count(),
        doctor_count=Doctor.query.count(),
        appointment_count=Appointment.query.count()
    )


# =========================================================
# PATIENTS
# =========================================================

@web_bp.route("/patients")
@admin_web_required
def patients_page():

    patients = Patient.query.all()

    return render_template(
        "patients.html",
        patients=patients
    )


@web_bp.route("/patients/new", methods=["GET", "POST"])
@admin_web_required
def new_patient():

    if request.method == "POST":

        try:

            patient = Patient(
                name=request.form["name"],
                age=int(request.form["age"]),
                gender=request.form["gender"],
                contact=request.form["contact"]
            )

            db.session.add(patient)
            db.session.commit()

            flash("Patient added successfully!")

            return redirect(
                url_for("web.patients_page")
            )

        except Exception as e:

            db.session.rollback()

            flash(f"Error adding patient: {e}")

    return render_template("patient_form.html")


@web_bp.route("/patients/<int:patient_id>/edit",
              methods=["GET", "POST"])
@admin_web_required
def edit_patient(patient_id):

    patient = db.session.get(
        Patient,
        patient_id
    )

    if not patient:

        return "Patient not found", 404

    if request.method == "POST":

        try:

            patient.name = request.form["name"]

            patient.age = int(
                request.form["age"]
            )

            patient.gender = request.form["gender"]

            patient.contact = request.form["contact"]

            db.session.commit()

            flash("Patient updated successfully!")

            return redirect(
                url_for("web.patients_page")
            )

        except Exception as e:

            db.session.rollback()

            flash(f"Error updating patient: {e}")

    return render_template(
        "patient_form.html",
        patient=patient
    )


@web_bp.route("/patients/<int:patient_id>/delete",
              methods=["POST"])
@admin_web_required
def delete_patient(patient_id):

    patient = db.session.get(
        Patient,
        patient_id
    )

    if not patient:

        return "Patient not found", 404

    db.session.delete(patient)
    db.session.commit()

    flash("Patient deleted successfully!")

    return redirect(
        url_for("web.patients_page")
    )


# =========================================================
# DOCTORS
# =========================================================

@web_bp.route("/doctors")
@admin_web_required
def doctors_page():

    doctors = Doctor.query.all()

    return render_template(
        "doctors.html",
        doctors=doctors
    )


@web_bp.route("/doctors/new",
              methods=["GET", "POST"])
@admin_web_required
def new_doctor():

    if request.method == "POST":

        try:

            doctor = Doctor(
                name=request.form["name"],
                specialization=request.form[
                    "specialization"
                ]
            )

            db.session.add(doctor)
            db.session.commit()

            flash("Doctor added successfully!")

            return redirect(
                url_for("web.doctors_page")
            )

        except Exception as e:

            db.session.rollback()

            flash(f"Error adding doctor: {e}")

    return render_template("doctor_form.html")


@web_bp.route("/doctors/<int:doctor_id>/edit",
              methods=["GET", "POST"])
@admin_web_required
def edit_doctor(doctor_id):

    doctor = db.session.get(
        Doctor,
        doctor_id
    )

    if not doctor:

        return "Doctor not found", 404

    if request.method == "POST":

        try:

            doctor.name = request.form["name"]

            doctor.specialization = request.form[
                "specialization"
            ]

            db.session.commit()

            flash("Doctor updated successfully!")

            return redirect(
                url_for("web.doctors_page")
            )

        except Exception as e:

            db.session.rollback()

            flash(f"Error updating doctor: {e}")

    return render_template(
        "doctor_form.html",
        doctor=doctor
    )


@web_bp.route("/doctors/<int:doctor_id>/delete",
              methods=["POST"])
@admin_web_required
def delete_doctor(doctor_id):

    doctor = db.session.get(
        Doctor,
        doctor_id
    )

    if not doctor:

        return "Doctor not found", 404

    linked_user = User.query.filter_by(
        doctor_id=doctor_id
    ).first()

    if linked_user:

        flash(
            "Cannot delete this doctor because "
            "a login account is linked to this doctor."
        )

        return redirect(
            url_for("web.doctors_page")
        )

    existing_appointment = Appointment.query.filter_by(
        doctor_id=doctor_id
    ).first()

    if existing_appointment:

        flash(
            "Cannot delete this doctor because "
            "appointments are assigned to this doctor."
        )

        return redirect(
            url_for("web.doctors_page")
        )

    db.session.delete(doctor)
    db.session.commit()

    flash("Doctor deleted successfully!")

    return redirect(
        url_for("web.doctors_page")
    )


# =========================================================
# APPOINTMENTS
# =========================================================

@web_bp.route("/appointments")
@doctor_or_admin_web_required
def appointments_page():

    user = get_logged_in_user()

    if session.get("role") == "admin":

        appointments = Appointment.query.all()

    else:

        appointments = Appointment.query.filter_by(
            doctor_id=user.doctor_id
        ).all()

    return render_template(
        "appointments.html",
        appointments=appointments
    )


@web_bp.route("/appointments/new",
              methods=["GET", "POST"])
@admin_web_required
def new_appointment():

    patients = Patient.query.all()
    doctors = Doctor.query.all()

    if request.method == "POST":

        try:

            appointment = Appointment(

                patient_id=int(
                    request.form["patient_id"]
                ),

                doctor_id=int(
                    request.form["doctor_id"]
                ),

                date=datetime.strptime(
                    request.form["date"],
                    "%Y-%m-%d"
                ).date(),

                diagnosis=request.form[
                    "diagnosis"
                ],

                status=request.form[
                    "status"
                ],

                recovery_date=(
                    datetime.strptime(
                        request.form["recovery_date"],
                        "%Y-%m-%d"
                    ).date()
                    if request.form.get(
                        "recovery_date"
                    )
                    else None
                )
            )

            db.session.add(appointment)
            db.session.commit()

            flash(
                "Appointment scheduled successfully!"
            )

            return redirect(
                url_for("web.appointments_page")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                f"Error scheduling appointment: {e}"
            )

    return render_template(
        "appointment_form.html",
        patients=patients,
        doctors=doctors
    )


@web_bp.route("/appointments/<int:appointment_id>/edit",
              methods=["GET", "POST"])
@doctor_or_admin_web_required
def edit_appointment(appointment_id):

    appointment = db.session.get(
        Appointment,
        appointment_id
    )

    if not appointment:

        return "Appointment not found", 404

    user = get_logged_in_user()

    # Doctor can edit only own appointment
    if session.get("role") == "doctor":

        if (
            not user
            or user.doctor_id != appointment.doctor_id
        ):

            flash(
                "You can only edit your own appointments."
            )

            return redirect(
                url_for("web.appointments_page")
            )

    patients = Patient.query.all()
    doctors = Doctor.query.all()

    if request.method == "POST":

        try:

            # Doctors cannot change patient or doctor
            if session.get("role") == "admin":

                appointment.patient_id = int(
                    request.form["patient_id"]
                )

                appointment.doctor_id = int(
                    request.form["doctor_id"]
                )

            appointment.date = datetime.strptime(
                request.form["date"],
                "%Y-%m-%d"
            ).date()

            appointment.diagnosis = request.form[
                "diagnosis"
            ]

            appointment.status = request.form[
                "status"
            ]

            appointment.recovery_date = (
                datetime.strptime(
                    request.form["recovery_date"],
                    "%Y-%m-%d"
                ).date()
                if request.form.get(
                    "recovery_date"
                )
                else None
            )

            db.session.commit()

            flash(
                "Appointment updated successfully!"
            )

            return redirect(
                url_for("web.appointments_page")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                f"Error updating appointment: {e}"
            )

    return render_template(
        "appointment_form.html",
        appointment=appointment,
        patients=patients,
        doctors=doctors
    )


@web_bp.route("/appointments/<int:appointment_id>/delete",
              methods=["POST"])
@admin_web_required
def delete_appointment(appointment_id):

    appointment = db.session.get(
        Appointment,
        appointment_id
    )

    if not appointment:

        return "Appointment not found", 404

    db.session.delete(appointment)
    db.session.commit()

    flash("Appointment deleted successfully!")

    return redirect(
        url_for("web.appointments_page")
    )


# =========================================================
# ANALYTICS
# =========================================================

@web_bp.route("/analytics")
@admin_web_required
def analytics_page():

    return render_template(
        "analytics.html"
    )


# =========================================================
# REPORTS
# =========================================================

@web_bp.route("/reports")
@admin_web_required
def reports_page():

    return render_template(
        "reports.html"
    )