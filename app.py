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

@app.route("/webhook", methods=["POST"])
def webhook():
    from_number = request.form.get("From", "")
    mensaje = request.form.get("Body", "").strip().lower()
    
    usuario = from_number.replace("whatsapp:", "")
    respuesta = MessagingResponse()

    # Detectar si es la primera vez que el usuario interactúa
    with sqlite3.connect("gastos.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM gastos WHERE usuario = ?", (usuario,))
        ya_existe = cursor.fetchone()[0] > 0

    if not ya_existe and mensaje not in ["1", "2", "3", "4", "resumen", "eliminar último", "eliminar ultimo"]:
        texto = (
            "👋 *¡Bienvenido/a al Bot de Gastos!* 🎉\n\n"
            "📲 *Comandos disponibles:*\n"
            "1 – Registrar un gasto\n"
            "2 – Ver resumen del día\n"
            "3 – Eliminar último gasto\n"
            "4 – Mostrar esta ayuda\n\n"
            "O escribí directamente:\n"
            "• *Gasté 8000 en kiosko* – para registrar un gasto\n"
            "• *Resumen* – para ver tus gastos del día\n"
            "• *Eliminar último* – para corregir un error"
        )
        respuesta.message(texto)
        return Response(str(respuesta), mimetype="application/xml")

    # Comando 1 – Instrucción para registrar gasto
    if mensaje == "1":
        texto = "✍️ Para registrar un gasto, escribí:\nEjemplo: *Gasté 8000 en kiosko*"
        respuesta.message(texto)
        return Response(str(respuesta), mimetype="application/xml")

    # Comando 2 – Mostrar resumen del día
    if mensaje == "2" or mensaje == "resumen":
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

    # Comando 3 – Eliminar último gasto
    if mensaje == "3" or mensaje == "eliminar último" or mensaje == "eliminar ultimo":
        with sqlite3.connect("gastos.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, monto, categoria, fecha
                FROM gastos
                WHERE usuario = ?
                ORDER BY fecha DESC
                LIMIT 1
            """, (usuario,))
            ultimo = cursor.fetchone()

            if ultimo:
                gasto_id, monto, categoria, fecha = ultimo
                cursor.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
                conn.commit()
                texto = f"✅ Último gasto eliminado:\n• {categoria} – ${monto} ({fecha})"
            else:
                texto = "No hay gastos para eliminar."

        respuesta.message(texto)
        return Response(str(respuesta), mimetype="application/xml")

    # Comando 4 – Ayuda
    if mensaje == "4" or mensaje == "ayuda":
        texto = (
            "📲 *Bot de Gastos – Comandos disponibles:*\n"
            "1 – Registrar un gasto\n"
            "2 – Ver resumen del día\n"
            "3 – Eliminar último gasto\n"
            "4 – Mostrar esta ayuda\n\n"
            "También podés escribir:\n"
            "• *Gasté 8000 en kiosko* – para registrar un gasto\n"
            "• *Resumen* – para ver tus gastos del día\n"
            "• *Eliminar último* – para corregir un error"
        )
        respuesta.message(texto)
        return Response(str(respuesta), mimetype="application/xml")

    # Si el mensaje contiene un gasto
    monto, categoria = extraer_datos(mensaje)
    if monto and categoria:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("gastos.db") as conn:
            conn.execute(
                "INSERT INTO gastos (monto, categoria, fecha, usuario) VALUES (?, ?, ?, ?)",
                (monto, categoria, fecha, usuario)
            )
        respuesta.message(f"Gasto de {monto} en {categoria} registrado, {usuario}.")
        return Response(str(respuesta), mimetype="application/xml")

    # Si no entendió el mensaje, mostrar menú
    texto = (
        "🤖 *No entendí tu mensaje.*\n\n"
        "📲 *Comandos disponibles:*\n"
        "1 – Registrar un gasto\n"
        "2 – Ver resumen del día\n"
        "3 – Eliminar último gasto\n"
        "4 – Mostrar esta ayuda\n\n"
        "O escribí directamente:\n"
        "• *Gasté 8000 en kiosko* – para registrar un gasto\n"
        "• *Resumen* – para ver tus gastos del día\n"
        "• *Eliminar último* – para corregir un error"
    )
    respuesta.message(texto)
    return Response(str(respuesta), mimetype="application/xml")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

