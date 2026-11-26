import re
from datetime import date

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from database import dbConnection
from models.patient import Patient


patients_bp = Blueprint("patients", __name__)
db = dbConnection()
patients = db["patients"]


def _parse_object_id(patient_id):
    try:
        return ObjectId(patient_id)
    except (InvalidId, TypeError):
        return None


def _get_patient_or_404(patient_id):
    object_id = _parse_object_id(patient_id)
    if object_id is None:
        abort(404)
    document = patients.find_one({"_id": object_id})
    if document is None:
        abort(404)
    return document


def _validate_patient_form(form, exclude_id=None):
    nombre = form.get("nombre", "").strip()
    dni = form.get("dni", "").strip()
    fecha_nacimiento = form.get("fecha_nacimiento", "").strip()
    telefono = form.get("telefono", "").strip()

    values = {
        "nombre": nombre,
        "dni": dni,
        "fecha_nacimiento": fecha_nacimiento,
        "telefono": telefono,
    }

    if not nombre or not dni or not fecha_nacimiento or not telefono:
        return values, "Todos los campos son obligatorios"
    if len(nombre) < 3 or len(nombre) > 120:
        return values, "El nombre debe tener entre 3 y 120 caracteres"
    if not re.fullmatch(r"\d{8}", dni):
        return values, "El DNI debe contener exactamente 8 dígitos"
    if not re.fullmatch(r"\d{9}", telefono):
        return values, "El teléfono debe contener exactamente 9 dígitos"

    try:
        birth_date = date.fromisoformat(fecha_nacimiento)
    except ValueError:
        return values, "La fecha de nacimiento no es válida"
    if birth_date > date.today():
        return values, "La fecha de nacimiento no puede ser futura"

    duplicate_query = {"dni": dni}
    if exclude_id is not None:
        duplicate_query["_id"] = {"$ne": exclude_id}
    if patients.find_one(duplicate_query):
        return values, f"El DNI {dni} ya está registrado"

    return values, None


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

    values, validation_error = _validate_patient_form(request.form)

    if validation_error:
        flash(validation_error, "danger")
        return render_template(
            "patients/new.html",
            today=date.today().isoformat(),
            **values,
        )

    patient = Patient(
        nombre=values["nombre"],
        dni=values["dni"],
        fecha_nacimiento=values["fecha_nacimiento"],
        telefono=values["telefono"],
    )
    patients.insert_one(patient.toDBCollection())
    flash(f"Paciente {values['nombre']} registrado exitosamente", "success")

    return redirect(url_for("patients.list_patients"))


@patients_bp.route("/pacientes/<string:patient_id>")
def detail_patient(patient_id):
    document = _get_patient_or_404(patient_id)
    patient = Patient.from_mongo(document)
    return render_template("patients/detail.html", patient=patient)


@patients_bp.route("/pacientes/<string:patient_id>/editar", methods=["GET", "POST"])
def edit_patient(patient_id):
    object_id = _parse_object_id(patient_id)
    if object_id is None:
        abort(404)
    document = patients.find_one({"_id": object_id})
    if document is None:
        abort(404)

    if request.method == "GET":
        patient = Patient.from_mongo(document)
        return render_template(
            "patients/edit.html",
            patient=patient,
            today=date.today().isoformat(),
        )

    values, validation_error = _validate_patient_form(
        request.form, exclude_id=object_id
    )

    if validation_error:
        flash(validation_error, "danger")
        patient = Patient(
            nombre=values["nombre"],
            dni=values["dni"],
            fecha_nacimiento=values["fecha_nacimiento"],
            telefono=values["telefono"],
            fecha_registro=document.get("fecha_registro"),
            id=patient_id,
        )
        return render_template(
            "patients/edit.html",
            patient=patient,
            today=date.today().isoformat(),
        )

    patients.update_one(
        {"_id": object_id},
        {
            "$set": {
                "nombre": values["nombre"],
                "dni": values["dni"],
                "fecha_nacimiento": values["fecha_nacimiento"],
                "telefono": values["telefono"],
            }
        },
    )
    flash(f"Paciente {values['nombre']} actualizado correctamente", "success")

    return redirect(url_for("patients.detail_patient", patient_id=patient_id))


@patients_bp.route("/pacientes/<string:patient_id>/eliminar", methods=["POST"])
def delete_patient(patient_id):
    document = _get_patient_or_404(patient_id)
    patients.delete_one({"_id": document["_id"]})
    flash(f"Paciente {document.get('nombre', '')} eliminado correctamente", "success")

    return redirect(url_for("patients.list_patients"))
