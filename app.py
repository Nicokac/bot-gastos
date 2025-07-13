# app.py
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
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
                fecha TEXT NOT NULL
            )
        ''')

@app.route("/mensaje", methods=["POST"])
def recibir_mensaje():
    data = request.json
    mensaje = data.get("mensaje", "")
    print("Recibí un mensaje")

    monto, categoria = extraer_datos(mensaje)
    if monto and categoria:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect("gastos.db") as conn:
            conn.execute("INSERT INTO gastos (monto, categoria, fecha) VALUES (?, ?, ?)",
                         (monto, categoria, fecha))
        return jsonify({"mensaje": f"Gasto de {monto} en {categoria} registrado."})
    else:
        return jsonify({"mensaje": "No pude entender el mensaje. Usá 'Gasté 8000 en kiosko'."})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
