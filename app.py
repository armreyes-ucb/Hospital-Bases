import os
import secrets

from flask import Flask

from routes import appointments_bp, patients_bp


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.register_blueprint(patients_bp)
app.register_blueprint(appointments_bp)


@app.errorhandler(404)
def not_found(error=None):
    return {
        "message": "No encontrado " + getattr(error, "description", ""),
        "status": "404 Not Found",
    }, 404


if __name__ == "__main__":
    app.run(debug=True, port=4000)
