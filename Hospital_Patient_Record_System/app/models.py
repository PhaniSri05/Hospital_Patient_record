from app.extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="admin")
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=True
    )

    
class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    contact = db.Column(db.String(15), nullable=False, unique=True)

    appointments = db.relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan"
    )


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)

    appointments = db.relationship(
        "Appointment",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    date = db.Column(db.Date, nullable=False)
    diagnosis = db.Column(db.String(255), nullable=False)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Under Treatment"
    )

    # Used for calculating recovery time
    recovery_date = db.Column(db.Date, nullable=True)

    patient = db.relationship(
        "Patient",
        back_populates="appointments"
    )

    doctor = db.relationship(
        "Doctor",
        back_populates="appointments"
    )