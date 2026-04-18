"""
main.py — Punto de entrada del agente comparador de precios.
Ejecuta este archivo para usar el agente.

Uso:
    python main.py
    python main.py "iPhone 15 Pro Max 256GB"
"""

import sys
from agent import AgenteComparadorPrecios


def modo_interactivo():
    """Modo conversacional: el agente espera consultas en un bucle."""
    print("\n" + "╔" + "═"*53 + "╗")
    print("║     🛒  AGENTE COMPARADOR DE PRECIOS v1.0       ║")
    print("║         Encuentra el mejor precio al instante   ║")
    print("╚" + "═"*53 + "╝")
    print("\nEscribe el producto que quieres comprar.")
    print("Escribe 'salir' para terminar.\n")

    agente = AgenteComparadorPrecios()

    while True:
        try:
            consulta = input("🛍️  ¿Qué quieres comparar? → ").strip()

            if not consulta:
                continue

            if consulta.lower() in ("salir", "exit", "quit", "q"):
                print("\n👋 ¡Hasta luego! Espero haberte ayudado a ahorrar.")
                break

            # Ejecutar el agente y mostrar la respuesta
            respuesta = agente.ejecutar(consulta, verbose=True)
            print(f"\n{respuesta}\n")
            print("─" * 55)

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            print("Asegúrate de que ANTHROPIC_API_KEY esté configurada correctamente.")


def modo_argumento(producto: str):
    """Modo directo: busca un producto pasado como argumento."""
    agente = AgenteComparadorPrecios()
    respuesta = agente.ejecutar(producto, verbose=True)
    print(f"\n{respuesta}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Ejecutado con argumento: python main.py "nombre del producto"
        producto = " ".join(sys.argv[1:])
        modo_argumento(producto)
    else:
        # Ejecutado sin argumentos: modo interactivo
        modo_interactivo()
