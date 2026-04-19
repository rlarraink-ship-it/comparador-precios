"""
app.py — Servidor web Flask para el agente comparador de precios.
Expone una interfaz web accesible desde cualquier navegador.

Ejecutar:
    python3 app.py
Luego abrir: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, stream_with_context, Response
from agent import AgenteComparadorPrecios
import json
import traceback

import os
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))
agente = AgenteComparadorPrecios()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/buscar", methods=["POST"])
def buscar():
    "@app.route("/buscar", methods=["POST"])
def buscar():
    data = request.get_json()
    producto = data.get("producto", "").strip()
    modo = data.get("modo", "todo")

    if not producto:
        return jsonify({"error": "Escribe un producto para buscar."}), 400

    try:
        if modo == "farmacias":
            from tools import buscar_en_ahumada, buscar_en_salcobrand, buscar_en_drsimi, buscar_en_cruzverde
            farmacias = [
                buscar_en_ahumada(producto),
                buscar_en_salcobrand(producto),
                buscar_en_drsimi(producto),
                buscar_en_cruzverde(producto),
            ]
            links = "\n".join(
                f"🔗 {f['fuente']}: {f['url_directa']}"
                for f in farmacias if f.get("url_directa")
            )
            resultado = f"💊 Busca {producto} en cada farmacia:\n\n{links}"
            return jsonify({"resultado": resultado, "producto": producto})

        resultado = agente.ejecutar(producto, modo=modo, verbose=True)
        return jsonify({"resultado": resultado, "producto": producto})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500