from datetime import date, time

from bson import ObjectId
from flask import Blueprint, flash, redirect, render_template, request, url_for

from database import dbConnection


appointments_bp = Blueprint("appointments", __name__)
db = dbConnection()
OPENING_TIME = time(8)
CLOSING_TIME = time(18)


@appointments_bp.route("/citas/nueva", methods=["GET", "POST"])
def new_appointment():
    values = {
        field: request.form.get(field, "").strip()
        for field in ("paciente_id", "medico_id", "fecha", "hora")
    }
    patients = list(db["patients"].find({}, {"nombre": 1, "dni": 1}).sort("nombre", 1))
    doctors = list(db["doctors"].find({}, {"nombre": 1}).sort("nombre", 1))

    if request.method == "POST":
        error = validate_appointment(values, patients, doctors)
        if error is None:
            db["appointments"].insert_one({
                "paciente_id": ObjectId(values["paciente_id"]),
                "medico_id": ObjectId(values["medico_id"]),
                "fecha": values["fecha"],
                "hora": values["hora"],
            })
            flash("Cita médica agendada correctamente.", "success")
            return redirect(url_for("appointments.new_appointment"), code=303)
        flash(error, "danger")

    return render_template(
        "appointments/schedule.html",
        patients=patients,
        doctors=doctors,
        values=values,
        opening_time=OPENING_TIME.strftime("%H:%M"),
        closing_time=CLOSING_TIME.strftime("%H:%M"),
    )


def validate_appointment(values, patients, doctors):
    if not any(str(patient["_id"]) == values["paciente_id"] for patient in patients):
        return "Selecciona un paciente existente."
    if not any(str(doctor["_id"]) == values["medico_id"] for doctor in doctors):
        return "Selecciona un médico de la lista."

    try:
        appointment_date = date.fromisoformat(values["fecha"])
    except ValueError:
        return "Selecciona una fecha válida."
    if appointment_date.isoformat() != values["fecha"]:
        return "Selecciona una fecha válida."

    try:
        appointment_time = time.fromisoformat(values["hora"])
    except ValueError:
        return "Selecciona una hora válida entre las 08:00 y las 18:00."
    if appointment_time.strftime("%H:%M") != values["hora"]:
        return "Selecciona una hora válida entre las 08:00 y las 18:00."
    if not OPENING_TIME <= appointment_time <= CLOSING_TIME:
        return "Selecciona una hora entre las 08:00 y las 18:00."

    return None
