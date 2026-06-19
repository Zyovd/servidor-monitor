import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request

app = Flask(__name__)

# Diccionario en memoria para almacenar el estado de las computadoras
computadoras = {}

# Configuración de alertas por correo usando las variables de entorno de Render
EMAIL_USER = os.environ.get("EMAIL_USER", "soportephygital@gmail.com")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_DESTINO = "soportephygital@gmail.com"


def enviar_correo_alerta(id_pc):
    """Función para enviar un correo seguro vía SMTP TLS cuando una PC se desconecta"""
    if not EMAIL_PASS:
        print(
            "[ALERTA CORREO] No se pudo enviar: Falta configurar la variable EMAIL_PASS en Render."
        )
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_DESTINO
        msg["Subject"] = f"🚨 ALERTA: {id_pc} se encuentra FUERA DE LÍNEA"

        cuerpo = f"El sistema de monitoreo informa que el equipo '{id_pc}' ha dejado de reportarse por más de 2 minutos."
        msg.attach(MIMEText(cuerpo, "plain"))

        # Conexión al servidor SMTP de Gmail (Puerto seguro 587)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_DESTINO, msg.as_string())
        server.quit()
        print(f"[CORREO] ¡Alerta enviada con éxito para {id_pc}!")
    except Exception as e:
        print(f"[CORREO ERROR] No se pudo enviar el correo: {e}")


def verificar_y_actualizar_estados():
    """Revisa los tiempos y marca como Offline si pasaron más de 2 minutos (120 segundos)"""
    zona_mx = ZoneInfo("America/Mexico_City")
    ahora = datetime.now(zona_mx)

    for id_pc, info in computadoras.items():
        try:
            ult_conexion = datetime.strptime(
                info["ultima_conexion"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=zona_mx)
            diferencia = (ahora - ult_conexion).total_seconds()

            if diferencia > 120 and info["status"] == "Online":
                computadoras[id_pc]["status"] = "Offline"
                enviar_correo_alerta(id_pc)
        except Exception as e:
            print(f"Error procesando tiempos para {id_pc}: {e}")


@app.route("/", methods=["GET"])
def inicio():
    return "Servidor Monitor Activo y Corriendo."


@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    try:
        datos = request.get_json()
        if not datos or "id_pc" not in datos:
            return jsonify({"error": "Falta el id_pc"}), 400

        id_pc = datos["id_pc"]
        status = "Online"

        zona_mx = ZoneInfo("America/Mexico_City")
        ahora = datetime.now(zona_mx).strftime("%Y-%m-%d %H:%M:%S")

        computadoras[id_pc] = {"status": status, "ultima_conexion": ahora}
        return jsonify({"mensaje": "Heartbeat recibido"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/estados", methods=["GET"])
def mostrar_estados():
    verificar_y_actualizar_estados()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="10">
        <title>Monitoreo de Equipos</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9; color: #333; }
            h1 { color: #2c3e50; }
            .buscador-container { margin-bottom: 20px; }
            #buscador { padding: 10px; width: 300px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; }
            table { width: 100%; border-collapse: collapse; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #34495e; color: white; }
            tr:hover { background-color: #f1f1f1; }
            .badge { padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; display: inline-block; }
            .online { background-color: #d4edda; color: #155724; }
            .offline { background-color: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>

        <h1>📋 Panel de Monitoreo de Equipos</h1>
        
        <div class="buscador-container">
            <input type="text" id="buscador" onkeyup="filtrarTabla()" placeholder="Buscar equipo por nombre (ej. 17)...">
        </div>

        <table id="tabla-equipos">
            <thead>
                <tr>
                    <th>Nombre de la Computadora</th>
                    <th>Estado</th>
                    <th>Última Actualización</th>
                    <th>Indicador</th>
                </tr>
            </thead>
            <tbody>
    """

    for id_pc, info in computadoras.items():
        if info["status"] == "Online":
            clase_status = "online"
            icono = "✔️"
        else:
            clase_status = "offline"
            icono = "❌"

        html += f"""
                <tr>
                    <td><b>{id_pc}</b></td>
                    <td><span class="badge {clase_status}">{info['status']}</span></td>
                    <td>{info['ultima_conexion']}</td>
                    <td style="font-size: 20px; padding-left: 25px;">{icono}</td>
                </tr>
        """

    html += """
            </tbody>
        </table>

        <script>
            function filtrarTabla() {
                let input = document.getElementById("buscador");
                let filter = input.value.toUpperCase();
                let table = document.getElementById("tabla-equipos");
                let tr = table.getElementsByTagName("tr");

                for (let i = 1; i < tr.length; i++) {
                    let td = tr[i].getElementsByTagName("td")[0];
                    if (td) {
                        let txtValue = td.textContent || td.innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            tr[i].style.display = "";
                        } else {
                            tr[i].style.display = "none";
                        }
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)