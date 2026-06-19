import os
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# Diccionario para guardar los estados de las computadoras
computadoras_estado = {}


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    datos = request.get_json()
    if not datos or "id_pc" not in datos or "status" not in datos:
        return jsonify({"error": "Datos inválidos"}), 400

    id_pc = datos["id_pc"]
    status = datos["status"]

    # Guardamos el estado y la hora actual del servidor
    computadoras_estado[id_pc] = {
        "status": status,
        "ultima_conexion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print(f"[NUBE] {id_pc} reportó estado: {status}")
    return jsonify({"mensaje": f"Estado de {id_pc} recibido"}), 200


@app.route("/estados", methods=["GET"])
def ver_estados():
    """Ruta para que tú entres desde el navegador a ver cómo están las PCs."""
    # Retorna un JSON limpio con el estatus de cada máquina
    return jsonify(computadoras_estado), 200


if __name__ == "__main__":
    # Render maneja los puertos automáticamente
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)