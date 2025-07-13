# app.py
from flask import Flask, request, jsonify, Response
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, date
import sqlite3
from utils import extraer_datos

app = Flask(__name__)

# Inicializa la base de datos
def init_db():
    with sqlite3.connect("gastos.db") as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monto INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                fecha TEXT NOT NULL,
                usuario TEXT NOT NULL
            )
        ''')

@app.route("/mensaje", methods=["POST"])
def recibir_mensaje():
    data = request.json
    mensaje = data.get("mensaje", "")
    usuario = data.get("usuario", "desconocido")  # Simulado por ahora
    print("Recibí un mensaje")

    monto, categoria = extraer_datos(mensaje)
    if monto and categoria:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("gastos.db") as conn:
            conn.execute("INSERT INTO gastos (monto, categoria, fecha, usuario) VALUES (?, ?, ?, ?)",
                         (monto, categoria, fecha, usuario))
        return jsonify({"mensaje": f"Gasto de {monto} en {categoria} registrado para {usuario}."})
    else:
        return jsonify({"mensaje": "No pude entender el mensaje. Usá 'Gasté 8000 en kiosko'."})

@app.route("/resumen", methods=["POST"])
def resumen():
    data = request.json
    usuario = data.get("usuario", "desconocido")  # Simulado

    hoy = date.today().isoformat()
    with sqlite3.connect("gastos.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT categoria, SUM(monto)
            FROM gastos
            WHERE fecha LIKE ? AND usuario = ?
            GROUP BY categoria
        """, (f"{hoy}%", usuario))
        resultados = cursor.fetchall()

    resumen = [{"categoria": fila[0], "total": fila[1]} for fila in resultados]
    total_gastado = sum(fila[1] for fila in resultados)

    return jsonify({
        "usuario": usuario,
        "resumen": resumen,
        "total_gastado": total_gastado
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    from_number = request.form.get("From", "")
    mensaje = request.form.get("Body", "").strip().lower()
    
    usuario = from_number.replace("whatsapp:", "")
    respuesta = MessagingResponse()

    if mensaje == "resumen":
        hoy = date.today().isoformat()
        with sqlite3.connect("gastos.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT categoria, SUM(monto)
                FROM gastos
                WHERE fecha LIKE ? AND usuario = ?
                GROUP BY categoria
            """, (f"{hoy}%", usuario))
            resultados = cursor.fetchall()

        if resultados:
            texto = "🧾 *Resumen de hoy:*\n"
            total = 0
            for cat, monto in resultados:
                texto += f"• {cat}: ${monto}\n"
                total += monto
            texto += f"*Total gastado:* ${total}"
        else:
            texto = "No registraste gastos hoy."

        respuesta.message(texto)
        return Response(str(respuesta), mimetype="application/xml")    

    monto, categoria = extraer_datos(mensaje)
    if monto and categoria:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("gastos.db") as conn:
            conn.execute(
                "INSERT INTO gastos (monto, categoria, fecha, usuario) VALUES (?, ?, ?, ?)",
                (monto, categoria, fecha, usuario)
            )
        respuesta.message(f"Gasto de {monto} en {categoria} registrado, {usuario}.")
    else:
        respuesta.message("No entendí tu mensaje. Usá 'Gasté 8000 en kiosko'.")

    return str(respuesta)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
