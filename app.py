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

app = Flask(__name__)
agente = AgenteComparadorPrecios()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/buscar", methods=["POST"])
def buscar():
    """Endpoint que recibe el producto y retorna la comparación como JSON."""
    data = request.get_json()
    producto = data.get("producto", "").strip()
    modo = data.get("modo", "todo")

    if not producto:
        return jsonify({"error": "Escribe un producto para buscar."}), 400

    try:
        # Ejecutar el agente (verbose=False para no imprimir en terminal)
        resultado = agente.ejecutar(producto, modo=modo, verbose=True)
        return jsonify({"resultado": resultado, "producto": producto})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n🌐 Servidor iniciado en: http://localhost:5000")
    print("   Comparte esta URL con amigos en tu misma red WiFi:")
    print("   http://TU-IP-LOCAL:5000  (ejecuta 'ipconfig getifaddr en0' para ver tu IP)\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
