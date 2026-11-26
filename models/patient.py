from datetime import datetime


class Patient:
    def __init__(
        self,
        nombre,
        dni,
        fecha_nacimiento,
        telefono,
        fecha_registro=None,
    ):
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
        return Patient(
            document.get("nombre", ""),
            document.get("dni", ""),
            document.get("fecha_nacimiento", ""),
            document.get("telefono", ""),
            document.get("fecha_registro", datetime.utcnow()),
        )
