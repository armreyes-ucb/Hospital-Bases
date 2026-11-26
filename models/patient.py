from datetime import datetime


class Patient:
    def __init__(
        self,
        nombre,
        dni,
        fecha_nacimiento,
        telefono,
        fecha_registro=None,
        id=None,
    ):
        self.id = id
        self.nombre = nombre
        self.dni = dni
        self.fecha_nacimiento = fecha_nacimiento
        self.telefono = telefono
        self.fecha_registro = fecha_registro or datetime.utcnow()

    def toDBCollection(self):
        return {
            "nombre": self.nombre,
            "dni": self.dni,
            "fecha_nacimiento": self.fecha_nacimiento,
            "telefono": self.telefono,
            "fecha_registro": self.fecha_registro,
        }

    @staticmethod
    def from_mongo(document):
        document_id = document.get("_id")
        return Patient(
            nombre=document.get("nombre", ""),
            dni=document.get("dni", ""),
            fecha_nacimiento=document.get("fecha_nacimiento", ""),
            telefono=document.get("telefono", ""),
            fecha_registro=document.get("fecha_registro", datetime.utcnow()),
            id=str(document_id) if document_id is not None else None,
        )
