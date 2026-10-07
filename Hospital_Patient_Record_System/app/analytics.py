from flask import Blueprint, jsonify

import pandas as pd
import numpy as np

from app.models import Appointment


analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics", methods=["GET"])
def analytics():

    appointments = Appointment.query.all()

    if not appointments:

        return jsonify({
            "message": "No appointment data available"
        }), 200


    data = []

    for appointment in appointments:

        data.append({

            "id": appointment.id,

            "patient_id": appointment.patient_id,

            "doctor_id": appointment.doctor_id,

            "date": appointment.date,

            "diagnosis": appointment.diagnosis,

            "status": appointment.status,

            "recovery_date": appointment.recovery_date

        })


    df = pd.DataFrame(data)


    # -----------------------------------------------------
    # Date conversion
    # -----------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"]
    )

    df["recovery_date"] = pd.to_datetime(
        df["recovery_date"],
        errors="coerce"
    )


    # -----------------------------------------------------
    # Recovery time
    # -----------------------------------------------------

    df["recovery_time"] = (
        df["recovery_date"] - df["date"]
    ).dt.days


    # -----------------------------------------------------
    # Most common diagnoses
    # -----------------------------------------------------

    common_diagnoses = (
        df["diagnosis"]
        .str.strip()
        .str.title()
        .value_counts()
        .to_dict()
    )


    # -----------------------------------------------------
    # Average recovery time
    # Only recovered patients
    # -----------------------------------------------------

    recovery_df = df[
        (df["status"] == "Recovered")
        & (df["recovery_time"].notna())
        & (df["recovery_time"] >= 0)
    ]


    if not recovery_df.empty:

        average_recovery = (
            recovery_df
            .groupby("diagnosis")["recovery_time"]
            .mean()
            .round(2)
            .to_dict()
        )

    else:

        average_recovery = {}


    # -----------------------------------------------------
    # Status distribution
    # -----------------------------------------------------

    status_distribution = (
        df["status"]
        .value_counts()
        .to_dict()
    )


    # -----------------------------------------------------
    # Doctor performance
    # -----------------------------------------------------

    doctor_performance = []


    for doctor_id, group in df.groupby("doctor_id"):

        total_patients = (
            group["patient_id"]
            .nunique()
        )


        recovered_patients = (
            group[
                group["status"] == "Recovered"
            ]["patient_id"]
            .nunique()
        )


        if total_patients > 0:

            recovery_rate = np.round(
                (
                    recovered_patients
                    / total_patients
                ) * 100,
                2
            )

        else:

            recovery_rate = 0


        doctor_performance.append({

            "doctor_id": int(doctor_id),

            "patients_treated": int(
                total_patients
            ),

            "recovered": int(
                recovered_patients
            ),

            "recovery_rate": float(
                recovery_rate
            )

        })


    # -----------------------------------------------------
    # Appointment trends
    # -----------------------------------------------------

    appointment_trends = (
        df.groupby(
            df["date"].dt.strftime("%Y-%m-%d")
        )
        .size()
        .to_dict()
    )


    # -----------------------------------------------------
    # Final response
    # -----------------------------------------------------

    return jsonify({

        "most_common_diagnoses":
            common_diagnoses,

        "average_recovery_time_days":
            average_recovery,

        "doctor_performance":
            doctor_performance,

        "status_distribution":
            status_distribution,

        "appointment_trends":
            appointment_trends

    }), 200