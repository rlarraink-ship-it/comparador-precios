"""
agent.py — El cerebro del agente.
Busca en todas las tiendas en paralelo, con soporte para filtrar por modo.
"""

import os
import json
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from tools import (
    buscar_en_google_shopping,
    buscar_en_falabella,
    buscar_en_ripley,
    buscar_en_paris,
    buscar_en_mercadolibre,
    buscar_en_jumbo,
    buscar_en_tottus,
    buscar_en_lider,
    buscar_en_unimarc,
    buscar_en_santaisabel,
    buscar_en_acuenta,
    buscar_en_ahumada,
    buscar_en_salcobrand,
    buscar_en_drsimi,
    buscar_en_cruzverde,
    buscar_en_cruzverde,
    buscar_en_salcobrand,
    buscar_en_ahumada,
    buscar_en_drsimi,
    comparar_precios,
)

TIENDAS_RETAIL = [
    ("Google Shopping",  lambda p: buscar_en_google_shopping(p, "CL")),
    ("Falabella",        buscar_en_falabella),
    ("Ripley",           buscar_en_ripley),
    ("Paris",            buscar_en_paris),
    ("MercadoLibre",     buscar_en_mercadolibre),
]

TIENDAS_SUPER = [
    ("Jumbo",           buscar_en_jumbo),
    ("Lider",           buscar_en_lider),
    ("Tottus",          buscar_en_tottus),
    ("Santa Isabel",    buscar_en_santaisabel),
    ("Acuenta",         buscar_en_acuenta),
    ("Unimarc",         buscar_en_unimarc),
]

TIENDAS_FARMACIAS = [
    ("Cruz Verde",      buscar_en_cruzverde),
    ("Salcobrand",      buscar_en_salcobrand),
    ("Ahumada",         buscar_en_ahumada),
    ("Dr. Simi",        buscar_en_drsimi),
]

TODAS_LAS_TIENDAS = TIENDAS_RETAIL + TIENDAS_SUPER + TIENDAS_FARMACIAS

SYSTEM_PROMPT = """Eres un agente experto en comparación de precios para consumidores chilenos.

Recibirás los resultados de búsqueda de las tiendas ya recopilados.
Tu única tarea es analizar esos datos y presentar un resumen claro.

Formato de respuesta:
- Empieza con 🏆 y el mejor precio encontrado con la tienda
- Muestra el ranking de las 5 mejores opciones con precio y tienda
- Indica el ahorro potencial (precio más caro vs más barato)
- Da 1-2 consejos prácticos sobre envío, disponibilidad o equivalentes genéricos
- Si algunas tiendas no encontraron resultados, mencionalo brevemente
- Sé conciso y directo

Habla en español chileno."""


class AgenteComparadorPrecios:
    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "❌ No se encontró ANTHROPIC_API_KEY.\n"
                "Ejecuta: export ANTHROPIC_API_KEY=tu-clave-aqui"
            )
        self.cliente = anthropic.Anthropic(api_key=api_key.strip())
        self.modelo = "claude-sonnet-4-6"

    def ejecutar(self, consulta: str, modo: str = "todo", verbose: bool = True) -> str:
        """
        modo: "todo"     → todas las tiendas
              "super"    → solo supermercados
              "farmacia" → solo farmacias
        """
        if verbose:
            print(f"\n{'='*55}")
            print(f"🔍 Buscando: {consulta} [{modo}]")
            print(f"{'='*55}")

        if modo == "super":
            tiendas = TIENDAS_SUPER
        elif modo == "farmacia":
            tiendas = TIENDAS_FARMACIAS
        else:
            tiendas = TODAS_LAS_TIENDAS

        # ── Paso 1: buscar en paralelo ────────────────────────────────────────
        resultados_acumulados = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futuros = {executor.submit(fn, consulta): nombre for nombre, fn in tiendas}
            for futuro in as_completed(futuros):
                nombre = futuros[futuro]
                try:
                    resultado = futuro.result()
                    resultados_acumulados.append(resultado)
                    if verbose:
                        n = resultado.get("total_resultados", 0)
                        print(f"  {'✓' if n else '–'} {nombre}: {n or 'sin'} resultados")
                except Exception as e:
                    if verbose:
                        print(f"  ✗ {nombre}: error — {e}")

        # ── Paso 2: comparar ──────────────────────────────────────────────────
        comparacion = comparar_precios(resultados_acumulados)
        if verbose:
            total = comparacion.get("resumen", {}).get("total_ofertas", 0)
            print(f"\n📊 Comparando {total} ofertas...")

        # ── Paso 3: Claude redacta el resumen ─────────────────────────────────
        modo_texto = {
            "super": "Solo supermercados",
            "farmacia": "Solo farmacias",
            "todo": "Todas las tiendas"
        }.get(modo, "Todas las tiendas")

        contexto = (
            f"El usuario busca: {consulta}\n"
            f"Modo de búsqueda: {modo_texto}\n\n"
            f"Resultados:\n{json.dumps(comparacion, ensure_ascii=False, indent=2)}\n\n"
            f"Tiendas consultadas:\n"
            + "\n".join(f"- {r.get('fuente', '?')}: {r.get('total_resultados', 0)} resultados"
                        for r in resultados_acumulados)
        )

        respuesta = self.cliente.messages.create(
            model=self.modelo,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": contexto}],
        )

        if verbose:
            print(f"\n{'─'*55}\n✅ Análisis completado\n")

        return respuesta.content[0].text
