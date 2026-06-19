import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request

app = Flask(__name__)

# Diccionario en memoria para almacenar el estado de las computadoras
computadoras = {}


@app.route("/", methods=["GET"])
def inicio():
    return "Servidor Monitor Activo y Corriendo en la Nube."


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    try:
        datos = request.get_json()
        if not datos or "id_pc" not in datos:
            return jsonify({"error": "Falta el id_pc"}), 400

        id_pc = datos["id_pc"]
        status = datos.get("status", "Online")

        # Forzar que la hora registrada sea la de México (GMT-6)
        zona_mx = ZoneInfo("America/Mexico_City")
        ahora = datetime.now(zona_mx).strftime("%Y-%m-%d %H:%M:%S")

        # Guardamos o actualizamos la info de la PC
        computadoras[id_pc] = {"status": status, "ultima_conexion": ahora}

        print(f"[HEARTBEAT] {id_pc} se reporta: {status} a las {ahora}")
        return jsonify({"mensaje": "Heartbeat recibido correctamente"}), 200

    except Exception as e:
        return jsonify({"error": f"Error en el servidor: {str(e)}"}), 500


@app.route("/estados", methods=["GET"])
def mostrar_estados():
    # Esta línea HTML obliga al navegador a actualizarse automáticamente cada 5 segundos
    cabecera_refresh = '<meta http-equiv="refresh" content="5">'

    # Formateamos el diccionario para que se vea ordenado y legible en pantalla
    json_bonito = json.dumps(computadoras, indent=4)

    return f"{cabecera_refresh}<h1>Monitoreo de Equipos</h1><pre>{json_bonito}</pre>"


@app.route("/ver_estados", methods=["GET"])
def ver_estados_json():
    # Ruta por si necesitas consumir los datos puros en formato JSON desde otra app
    return jsonify(computadoras)


if __name__ == "__main__":
    # Render asigna el puerto mediante una variable de entorno, por eso usamos el puerto 5000 por defecto
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)
