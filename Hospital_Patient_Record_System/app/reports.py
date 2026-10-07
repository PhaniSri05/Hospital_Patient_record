from flask import Blueprint, send_file, jsonify, request
from datetime import datetime
import pandas as pd
from io import BytesIO

from app.extensions import db
from app.models import Patient, Doctor, Appointment


reports_bp = Blueprint("reports", __name__)


# ---------------------------------------------------------
# Create DataFrame from appointments
# ---------------------------------------------------------

def get_dataframe():

    appointments = Appointment.query.all()

    data = []

    for appointment in appointments:

        data.append({
            "ID": appointment.id,
            "Patient ID": appointment.patient_id,
            "Doctor ID": appointment.doctor_id,
            "Date": appointment.date,
            "Diagnosis": appointment.diagnosis,
            "Status": appointment.status,
            "Recovery Date": appointment.recovery_date
        })

    return pd.DataFrame(data)


# ---------------------------------------------------------
# Export appointments as CSV
# ---------------------------------------------------------

@reports_bp.route("/reports/appointments.csv", methods=["GET"])
def export_csv():

    df = get_dataframe()

    if df.empty:
        return jsonify({
            "error": "No appointment data available"
        }), 404

    output = BytesIO()

    output.write(
        df.to_csv(index=False).encode("utf-8")
    )

    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="appointments_report.csv"
    )


# ---------------------------------------------------------
# Export appointments as Excel
# ---------------------------------------------------------

@reports_bp.route("/reports/appointments.xlsx", methods=["GET"])
def export_excel():

    df = get_dataframe()

    if df.empty:
        return jsonify({
            "error": "No appointment data available"
        }), 404

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Appointments"
        )

    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="appointments_report.xlsx"
    )


# ---------------------------------------------------------
# Upload appointment CSV
# ---------------------------------------------------------

@reports_bp.route("/reports/upload", methods=["POST"])
def upload_csv():

    if "file" not in request.files:

        return jsonify({
            "error": "CSV file is required"
        }), 400


    file = request.files["file"]


    if file.filename == "":

        return jsonify({
            "error": "No file selected"
        }), 400


    if not file.filename.lower().endswith(".csv"):

        return jsonify({
            "error": "Only CSV files are allowed"
        }), 400


    try:

        # Read CSV using Pandas
        df = pd.read_csv(file)


        # -------------------------------------------------
        # Clean column names
        # -------------------------------------------------

        df.columns = [
            str(column).strip()
            for column in df.columns
        ]


        # -------------------------------------------------
        # Accept exported report format also
        # -------------------------------------------------

        column_mapping = {

            "Patient ID": "patient_id",
            "Doctor ID": "doctor_id",
            "Date": "date",
            "Diagnosis": "diagnosis",
            "Status": "status",
            "Recovery Date": "recovery_date",

            # Also accept lowercase format
            "patient_id": "patient_id",
            "doctor_id": "doctor_id",
            "date": "date",
            "diagnosis": "diagnosis",
            "status": "status",
            "recovery_date": "recovery_date"
        }


        df = df.rename(
            columns=column_mapping
        )


        # -------------------------------------------------
        # Required columns
        # -------------------------------------------------

        required_columns = [
            "patient_id",
            "doctor_id",
            "date",
            "diagnosis",
            "status"
        ]


        missing = [
            column
            for column in required_columns
            if column not in df.columns
        ]


        if missing:

            return jsonify({
                "error": f"Missing columns: {missing}"
            }), 400


        # -------------------------------------------------
        # Validate status values
        # -------------------------------------------------

        allowed_statuses = [
            "Recovered",
            "Under Treatment",
            "Critical"
        ]


        count = 0


        # -------------------------------------------------
        # Insert appointments
        # -------------------------------------------------

        for _, row in df.iterrows():

            # Patient
            patient = db.session.get(
                Patient,
                int(row["patient_id"])
            )


            # Doctor
            doctor = db.session.get(
                Doctor,
                int(row["doctor_id"])
            )


            if not patient:

                continue


            if not doctor:

                continue


            # Date
            appointment_date = datetime.strptime(
                str(row["date"]),
                "%Y-%m-%d"
            ).date()


            # Recovery date
            recovery_date = None


            if (
                "recovery_date" in df.columns
                and pd.notna(row["recovery_date"])
                and str(row["recovery_date"]).strip() != ""
            ):

                recovery_date = datetime.strptime(
                    str(row["recovery_date"]),
                    "%Y-%m-%d"
                ).date()


            # Status
            status = str(
                row["status"]
            ).strip()


            if status not in allowed_statuses:

                return jsonify({
                    "error": (
                        f"Invalid status '{status}'. "
                        f"Allowed values are: "
                        f"{', '.join(allowed_statuses)}"
                    )
                }), 400


            # Create appointment
            appointment = Appointment(

                patient_id=int(
                    row["patient_id"]
                ),

                doctor_id=int(
                    row["doctor_id"]
                ),

                date=appointment_date,

                diagnosis=str(
                    row["diagnosis"]
                ).strip(),

                status=status,

                recovery_date=recovery_date
            )


            db.session.add(
                appointment
            )

            count += 1


        # Save changes
        db.session.commit()


        return jsonify({

            "message": "CSV uploaded successfully",

            "appointments_added": count

        }), 201


    except Exception as e:

        db.session.rollback()

        return jsonify({

            "error": str(e)

        }), 400