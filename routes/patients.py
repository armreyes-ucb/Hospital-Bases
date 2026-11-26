import re
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from database import dbConnection
from models.patient import Patient


patients_bp = Blueprint("patients", __name__)
db = dbConnection()
patients = db["patients"]


@patients_bp.route("/")
def home():
    return redirect(url_for("patients.list_patients"))


@patients_bp.route("/pacientes")
def list_patients():
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    search = request.args.get("search", request.args.get("q", "")).strip()
    dni_search = request.args.get("dni", "").strip()
    per_page = 10

    query = {}
    filters = []
    if search:
        filters.append(
            {
                "$or": [
                    {"nombre": {"$regex": re.escape(search), "$options": "i"}},
                    {"dni": search},
                ]
            }
        )
    if dni_search:
        filters.append({"dni": dni_search})
    if filters:
        query = filters[0] if len(filters) == 1 else {"$and": filters}

    total_patients = patients.count_documents(query)
    total_registered = patients.count_documents({})
    patients_cursor = (
        patients.find(query)
        .sort("fecha_registro", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )

    patients_list = [Patient.from_mongo(doc) for doc in patients_cursor]
    total_pages = (total_patients + per_page - 1) // per_page

    return render_template(
        "patients/list.html",
        patients=patients_list,
        page=page,
        total_pages=total_pages,
        total_patients=total_registered,
        filtered_patients=total_patients,
        search=search,
        dni_search=dni_search,
    )


@patients_bp.route("/pacientes/nuevo", methods=["GET", "POST"])
@patients_bp.route("/pacientes/new", methods=["GET", "POST"])
def new_patient():
    if request.method == "GET":
        return render_template("patients/new.html", today=date.today().isoformat())

    nombre = request.form.get("nombre", "").strip()
    dni = request.form.get("dni", "").strip()
    fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()
    telefono = request.form.get("telefono", "").strip()

    today = date.today()
    validation_error = None
    if not nombre or not dni or not fecha_nacimiento or not telefono:
        validation_error = "Todos los campos son obligatorios"
    elif len(nombre) < 3 or len(nombre) > 120:
        validation_error = "El nombre debe tener entre 3 y 120 caracteres"
    elif not re.fullmatch(r"\d{8}", dni):
        validation_error = "El DNI debe contener exactamente 8 dígitos"
    elif not re.fullmatch(r"\d{9}", telefono):
        validation_error = "El teléfono debe contener exactamente 9 dígitos"
    else:
        try:
            birth_date = date.fromisoformat(fecha_nacimiento)
            if birth_date > today:
                validation_error = "La fecha de nacimiento no puede ser futura"
        except ValueError:
            validation_error = "La fecha de nacimiento no es válida"

    if validation_error:
        flash(validation_error, "danger")
        return render_template(
            "patients/new.html",
            nombre=nombre,
            dni=dni,
            fecha_nacimiento=fecha_nacimiento,
            telefono=telefono,
            today=today.isoformat(),
        )

    existing = patients.find_one({"dni": dni})
    if existing:
        flash(f"El DNI {dni} ya está registrado", "danger")
        return render_template(
            "patients/new.html",
            nombre=nombre,
            dni=dni,
            fecha_nacimiento=fecha_nacimiento,
            telefono=telefono,
            today=date.today().isoformat(),
        )

    patient = Patient(
        nombre=nombre,
        dni=dni,
        fecha_nacimiento=fecha_nacimiento,
        telefono=telefono,
    )
    patients.insert_one(patient.toDBCollection())
    flash(f"Paciente {nombre} registrado exitosamente", "success")

    return redirect(url_for("patients.new_patient"))
