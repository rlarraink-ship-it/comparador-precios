"""
tools.py — Las herramientas que usa el agente para buscar precios.
Cada función es una "habilidad" que Claude puede invocar.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

# Cabeceras para simular un navegador real (evita bloqueos)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Pon tu clave SerpApi aquí (una sola vez para todas las tiendas) ─────────
# Regístrate gratis en https://serpapi.com (100 búsquedas/mes)
SERPAPI_KEY = "TU_CLAVE_SERPAPI_AQUI"


def buscar_en_google_shopping(producto: str, pais: str = "CL") -> dict:
    """
    Busca precios usando la API gratuita de SerpApi (Google Shopping).
    Requiere registrarse en serpapi.com para obtener una API key gratuita.
    Retorna una lista de resultados con tienda, precio y enlace.
    """
    if SERPAPI_KEY == "TU_CLAVE_SERPAPI_AQUI":
        return _datos_demo(producto)

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": producto,
        "gl": pais.lower(),
        "hl": "es",
        "api_key": SERPAPI_KEY,
        "num": 10,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        resultados = []
        for item in data.get("shopping_results", [])[:8]:
            precio_texto = item.get("price", "")
            precio_num = _extraer_numero(precio_texto)
            resultados.append({
                "tienda": item.get("source", "Desconocida"),
                "precio_texto": precio_texto,
                "precio_num": precio_num,
                "titulo": item.get("title", producto),
                "enlace": item.get("link", ""),
                "calificacion": item.get("rating", None),
                "envio": item.get("delivery", "No especificado"),
            })

        return {
            "producto_buscado": producto,
            "total_resultados": len(resultados),
            "resultados": resultados,
            "fuente": "Google Shopping",
        }

    except requests.RequestException as e:
        return {"error": f"Error al buscar en Google Shopping: {str(e)}", "resultados": []}


def buscar_en_falabella(producto: str) -> dict:
    """
    Busca precios directamente en Falabella Chile.
    Usa el buscador público de falabella.com.
    """
    url = "https://www.falabella.com/falabella-cl/search"
    params = {"Ntt": producto, "sortBy": "priceAsc"}

    try:
        time.sleep(random.uniform(0.5, 1.5))  # Pausa educada entre requests
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        resultados = []

        # Busca tarjetas de producto en la página
        tarjetas = soup.find_all(
            "div",
            class_=re.compile(r"product-card|pod-product", re.I),
            limit=6
        )

        for tarjeta in tarjetas:
            nombre_el = tarjeta.find(["h2", "b", "span"], class_=re.compile(r"pod-subTitle|product-name", re.I))
            precio_el = tarjeta.find("span", class_=re.compile(r"copy10|price|precio", re.I))

            if nombre_el and precio_el:
                precio_texto = precio_el.get_text(strip=True)
                precio_num = _extraer_numero(precio_texto)
                resultados.append({
                    "tienda": "Falabella",
                    "precio_texto": precio_texto,
                    "precio_num": precio_num,
                    "titulo": nombre_el.get_text(strip=True)[:80],
                    "enlace": "https://www.falabella.com/falabella-cl/search?Ntt=" + producto.replace(" ", "+"),
                    "envio": "Ver en sitio",
                })

        if not resultados:
            # Si el scraping falla (estructura cambió), retorna instrucción
            return {
                "producto_buscado": producto,
                "nota": "No se pudieron extraer precios automáticamente. Visita falabella.com directamente.",
                "resultados": [],
                "url_directa": f"https://www.falabella.com/falabella-cl/search?Ntt={producto.replace(' ', '+')}",
            }

        return {
            "producto_buscado": producto,
            "total_resultados": len(resultados),
            "resultados": resultados,
            "fuente": "Falabella Chile",
        }

    except requests.RequestException as e:
        return {"error": f"Error al conectar con Falabella: {str(e)}", "resultados": []}


def comparar_precios(resultados_tiendas: list) -> dict:
    """
    Recibe los resultados de varias tiendas y genera una comparación.
    Identifica el precio más bajo, más alto y el promedio.
    """
    todos = []
    for bloque in resultados_tiendas:
        for item in bloque.get("resultados", []):
            if item.get("precio_num") and item["precio_num"] > 0:
                todos.append(item)

    if not todos:
        return {"error": "No se encontraron precios válidos para comparar."}

    # Ordenar de menor a mayor precio
    todos_ordenados = sorted(todos, key=lambda x: x["precio_num"])

    precios = [x["precio_num"] for x in todos_ordenados]
    promedio = sum(precios) / len(precios)
    ahorro_maximo = precios[-1] - precios[0]

    return {
        "resumen": {
            "total_ofertas": len(todos_ordenados),
            "precio_minimo": precios[0],
            "precio_maximo": precios[-1],
            "precio_promedio": round(promedio, 0),
            "ahorro_potencial": ahorro_maximo,
            "mejor_oferta": todos_ordenados[0],
        },
        "ranking_completo": todos_ordenados,
    }


def buscar_en_ripley(producto: str) -> dict:
    """Busca precios directamente en Ripley Chile."""
    url = "https://simple.ripley.cl/search"
    params = {"query": producto}

    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        resultados = []

        tarjetas = soup.find_all("div", class_=re.compile(r"catalog-product-item|product-card", re.I), limit=6)

        for tarjeta in tarjetas:
            nombre_el = tarjeta.find(["p", "span", "h2"], class_=re.compile(r"product-title|item-title", re.I))
            precio_el = tarjeta.find("span", class_=re.compile(r"product-price|price", re.I))

            if nombre_el and precio_el:
                precio_texto = precio_el.get_text(strip=True)
                precio_num = _extraer_numero(precio_texto)
                if precio_num > 0:
                    resultados.append({
                        "tienda": "Ripley",
                        "precio_texto": precio_texto,
                        "precio_num": precio_num,
                        "titulo": nombre_el.get_text(strip=True)[:80],
                        "enlace": f"https://simple.ripley.cl/search?query={producto.replace(' ', '+')}",
                        "envio": "Ver en sitio",
                    })

        if not resultados:
            return {
                "producto_buscado": producto,
                "nota": "No se pudieron extraer precios de Ripley automáticamente.",
                "resultados": [],
                "url_directa": f"https://simple.ripley.cl/search?query={producto.replace(' ', '+')}",
            }

        return {
            "producto_buscado": producto,
            "total_resultados": len(resultados),
            "resultados": resultados,
            "fuente": "Ripley Chile",
        }

    except requests.RequestException as e:
        return {"error": f"Error al conectar con Ripley: {str(e)}", "resultados": []}


def buscar_en_paris(producto: str) -> dict:
    """Busca precios directamente en Paris Chile."""
    url = "https://www.paris.cl/search"
    params = {"q": producto}

    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        resultados = []

        tarjetas = soup.find_all("div", class_=re.compile(r"product-tile|product-card", re.I), limit=6)

        for tarjeta in tarjetas:
            nombre_el = tarjeta.find(["span", "h2", "p"], class_=re.compile(r"product-name|item-name|title", re.I))
            precio_el = tarjeta.find("span", class_=re.compile(r"price|precio", re.I))

            if nombre_el and precio_el:
                precio_texto = precio_el.get_text(strip=True)
                precio_num = _extraer_numero(precio_texto)
                if precio_num > 0:
                    resultados.append({
                        "tienda": "Paris",
                        "precio_texto": precio_texto,
                        "precio_num": precio_num,
                        "titulo": nombre_el.get_text(strip=True)[:80],
                        "enlace": f"https://www.paris.cl/search?q={producto.replace(' ', '+')}",
                        "envio": "Ver en sitio",
                    })

        if not resultados:
            return {
                "producto_buscado": producto,
                "nota": "No se pudieron extraer precios de Paris automáticamente.",
                "resultados": [],
                "url_directa": f"https://www.paris.cl/search?q={producto.replace(' ', '+')}",
            }

        return {
            "producto_buscado": producto,
            "total_resultados": len(resultados),
            "resultados": resultados,
            "fuente": "Paris Chile",
        }

    except requests.RequestException as e:
        return {"error": f"Error al conectar con Paris: {str(e)}", "resultados": []}


def buscar_en_mercadolibre(producto: str, pais: str = "CL") -> dict:
    """Busca precios en MercadoLibre. Soporta CL, MX, AR, CO, PE."""
    dominios = {
        "CL": "listado.mercadolibre.cl",
        "MX": "listado.mercadolibre.com.mx",
        "AR": "listado.mercadolibre.com.ar",
        "CO": "listado.mercadolibre.com.co",
        "PE": "listado.mercadolibre.com.pe",
    }
    dominio = dominios.get(pais.upper(), dominios["CL"])
    url = f"https://{dominio}/{producto.replace(' ', '-')}"

    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        resultados = []

        tarjetas = soup.find_all("li", class_=re.compile(r"ui-search-layout__item", re.I), limit=8)

        for tarjeta in tarjetas:
            nombre_el = tarjeta.find(["h2", "h3", "span"], class_=re.compile(r"ui-search-item__title", re.I))
            precio_el = tarjeta.find("span", class_=re.compile(r"andes-money-amount__fraction", re.I))
            envio_el  = tarjeta.find("span", class_=re.compile(r"ui-search-item__shipping", re.I))

            if nombre_el and precio_el:
                precio_texto = "$" + precio_el.get_text(strip=True)
                precio_num = _extraer_numero(precio_texto)
                envio = envio_el.get_text(strip=True) if envio_el else "Ver en sitio"
                if precio_num > 0:
                    resultados.append({
                        "tienda": f"MercadoLibre",
                        "precio_texto": precio_texto,
                        "precio_num": precio_num,
                        "titulo": nombre_el.get_text(strip=True)[:80],
                        "enlace": url,
                        "envio": envio,
                    })

        if not resultados:
            return {
                "producto_buscado": producto,
                "nota": "No se pudieron extraer precios de MercadoLibre automáticamente.",
                "resultados": [],
                "url_directa": url,
            }

        return {
            "producto_buscado": producto,
            "total_resultados": len(resultados),
            "resultados": resultados,
            "fuente": "MercadoLibre",
        }

    except requests.RequestException as e:
        return {"error": f"Error al conectar con MercadoLibre: {str(e)}", "resultados": []}


def _extraer_numero(texto: str) -> float:
    """Extrae el número de un texto de precio como '$1.299.990' → 1299990.0"""
    if not texto:
        return 0.0
    solo_nums = re.sub(r"[^\d]", "", texto)
    try:
        return float(solo_nums) if solo_nums else 0.0
    except ValueError:
        return 0.0


def _datos_demo(producto: str) -> dict:
    """Datos de ejemplo para demostración sin API key."""
    base = random.randint(200000, 800000)
    return {
        "producto_buscado": producto,
        "total_resultados": 5,
        "nota": "⚠️ Datos de DEMO. Agrega tu clave SerpApi para precios reales.",
        "resultados": [
            {"tienda": "TiendaMuestra A", "precio_texto": f"${base:,}".replace(",", "."),
             "precio_num": base, "titulo": producto, "enlace": "#", "envio": "Gratis"},
            {"tienda": "TiendaMuestra B", "precio_texto": f"${int(base*1.08):,}".replace(",", "."),
             "precio_num": int(base * 1.08), "titulo": producto, "enlace": "#", "envio": "$3.990"},
            {"tienda": "TiendaMuestra C", "precio_texto": f"${int(base*0.95):,}".replace(",", "."),
             "precio_num": int(base * 0.95), "titulo": producto, "enlace": "#", "envio": "Gratis"},
            {"tienda": "TiendaMuestra D", "precio_texto": f"${int(base*1.15):,}".replace(",", "."),
             "precio_num": int(base * 1.15), "titulo": producto, "enlace": "#", "envio": "Ver sitio"},
            {"tienda": "TiendaMuestra E", "precio_texto": f"${int(base*1.02):,}".replace(",", "."),
             "precio_num": int(base * 1.02), "titulo": producto, "enlace": "#", "envio": "$1.990"},
        ],
        "fuente": "Demo",
    }


def _buscar_supermercado_via_serpapi(producto: str, tienda: str, dominio: str) -> dict:
    """
    Busca precios de un supermercado usando SerpApi con filtro de sitio.
    Mucho más confiable que scraping directo ya que los supermercados bloquean bots.
    """
    SERPAPI_KEY = _get_serpapi_key()
    if not SERPAPI_KEY:
        return {
            "producto_buscado": producto,
            "nota": f"Agrega tu clave SerpApi en tools.py para buscar en {tienda}.",
            "resultados": [],
            "url_directa": f"https://{dominio}/search?q={producto.replace(' ', '+')}",
        }

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": f"{producto} {tienda}",
        "gl": "cl",
        "hl": "es",
        "api_key": SERPAPI_KEY,
        "num": 6,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Alias de nombres alternativos que usan los supermercados en Google
        aliases = {
            "walmart.cl":      ["walmart", "lider"],
            "unimarc.cl":      ["unimarc"],
            "jumbo.cl":        ["jumbo", "cencosud"],
            "tottus.cl":       ["tottus", "falabella"],
            "santaisabel.cl":  ["santa isabel", "santaisabel", "cencosud"],
            "farmaciasahumada.cl": ["ahumada", "farmacias ahumada"],
            "salcobrand.cl":      ["salcobrand"],
            "drogueriasimi.cl":   ["simi", "dr simi", "dr. simi"],
            "cruzverde.cl":       ["cruz verde", "cruzverde"],
            "acuenta.cl":      ["acuenta", "cencosud"],
            "cruzverde.cl":    ["cruz verde", "cruzverde"],
            "salcobrand.cl":   ["salcobrand"],
            "farmaciasahumada.cl": ["ahumada", "farmacias ahumada"],
            "drsimi.cl":       ["dr simi", "dr. simi", "simi"],
        }
        dominio_corto = dominio.replace("www.", "")
        terminos = [dominio_corto] + aliases.get(dominio_corto, [])

        resultados = []
        for item in data.get("shopping_results", [])[:10]:
            source = item.get("source", "").lower()
            link   = item.get("link", "").lower()
            # Acepta si cualquier término conocido aparece en source o link
            if not any(t in source or t in link for t in terminos):
                continue
            precio_texto = item.get("price", "")
            precio_num = _extraer_numero(precio_texto)
            if precio_num > 0:
                resultados.append({
                    "tienda": tienda,
                    "precio_texto": precio_texto,
                    "precio_num": precio_num,
                    "titulo": item.get("title", producto)[:80],
                    "enlace": item.get("link", f"https://{dominio}"),
                    "envio": item.get("delivery", "Ver en sitio"),
                })

        if not resultados:
            return {
                "producto_buscado": producto,
                "nota": f"No se encontraron resultados para {tienda} en Google Shopping.",
                "resultados": [],
                "url_directa": f"https://{dominio}",
            }

        return {
            "producto_buscado": producto,
            "total_resultados": len(resultados),
            "resultados": resultados,
            "fuente": tienda,
        }

    except requests.RequestException as e:
        return {"error": f"Error buscando en {tienda}: {str(e)}", "resultados": []}


def _get_serpapi_key() -> str:
    """Retorna la clave SerpApi global."""
    return None if SERPAPI_KEY == "TU_CLAVE_SERPAPI_AQUI" else SERPAPI_KEY


def buscar_en_jumbo(producto: str) -> dict:
    """Busca precios en Jumbo Chile vía Google Shopping."""
    return _buscar_supermercado_via_serpapi(producto, "Jumbo", "www.jumbo.cl")


def buscar_en_tottus(producto: str) -> dict:
    """Busca precios en Tottus Chile vía Google Shopping."""
    return _buscar_supermercado_via_serpapi(producto, "Tottus", "www.tottus.cl")


def buscar_en_lider(producto: str) -> dict:
    """Busca precios en Walmart/Lider Chile vía Google Shopping."""
    return _buscar_supermercado_via_serpapi(producto, "Walmart / Lider", "www.walmart.cl")


def buscar_en_unimarc(producto: str) -> dict:
    """Busca precios en Unimarc Chile vía Google Shopping."""
    return _buscar_supermercado_via_serpapi(producto, "Unimarc", "www.unimarc.cl")


def buscar_en_santaisabel(producto: str) -> dict:
    """Busca precios en Santa Isabel Chile vía Google Shopping."""
    return _buscar_supermercado_via_serpapi(producto, "Santa Isabel", "www.santaisabel.cl")


def buscar_en_acuenta(producto: str) -> dict:
    """Busca precios en Acuenta Chile vía Google Shopping."""
    return _buscar_supermercado_via_serpapi(producto, "Acuenta", "www.acuenta.cl")



def buscar_en_ahumada(producto: str) -> dict:
    """Retorna link directo a Farmacia Ahumada."""
    q = producto.replace(" ", "%20")
    return {
        "producto_buscado": producto,
        "resultados": [],
        "fuente": "Farmacia Ahumada",
        "nota": "Ver precios directamente",
        "url_directa": f"https://www.farmaciasahumada.cl/buscar?query={q}",
        "total_resultados": 0,
    }


def buscar_en_salcobrand(producto: str) -> dict:
    """Retorna link directo a Salcobrand."""
    q = producto.replace(" ", "%20")
    return {
        "producto_buscado": producto,
        "resultados": [],
        "fuente": "Salcobrand",
        "nota": "Ver precios directamente",
        "url_directa": f"https://salcobrand.cl/search?term={q}",
        "total_resultados": 0,
    }


def buscar_en_drsimi(producto: str) -> dict:
    """Retorna link directo a Dr. Simi."""
    q = producto.replace(" ", "%20")
    return {
        "producto_buscado": producto,
        "resultados": [],
        "fuente": "Dr. Simi",
        "nota": "Ver precios directamente",
        "url_directa": f"https://www.drogueriasimi.cl/search?q={q}",
        "total_resultados": 0,
    }


def buscar_en_cruzverde(producto: str) -> dict:
    """Retorna link directo a Cruz Verde."""
    q = producto.replace(" ", "%20")
    return {
        "producto_buscado": producto,
        "resultados": [],
        "fuente": "Cruz Verde",
        "nota": "Ver precios directamente",
        "url_directa": f"https://www.cruzverde.cl/search?query={q}",
        "total_resultados": 0,
    }


def _buscar_farmacia_playwright(producto: str, nombre: str, url: str, 
                                 selector_nombre: str, selector_precio: str) -> dict:
    """Busca precios en farmacias usando Playwright (navegador real)."""
    try:
        from playwright.sync_api import sync_playwright
        import time as _time

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="es-CL"
            )
            page = context.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            _time.sleep(2)  # Esperar que cargue el JS

            resultados = []
            try:
                items = page.query_selector_all(selector_nombre)
                precios = page.query_selector_all(selector_precio)

                for i, item in enumerate(items[:6]):
                    nombre_texto = item.inner_text().strip()[:80]
                    precio_texto = precios[i].inner_text().strip() if i < len(precios) else ""
                    precio_num = _extraer_numero(precio_texto)
                    if precio_num > 0 and nombre_texto:
                        resultados.append({
                            "tienda": nombre,
                            "precio_texto": precio_texto,
                            "precio_num": precio_num,
                            "titulo": nombre_texto,
                            "enlace": url,
                            "envio": "Ver en sitio",
                        })
            except Exception:
                pass

            browser.close()

        if not resultados:
            return {
                "producto_buscado": producto,
                "nota": f"No se encontraron precios en {nombre}.",
                "resultados": [],
                "url_directa": url,
            }

        return {
            "producto_buscado": producto,
            "total_resultados": len(resultados),
            "resultados": resultados,
            "fuente": nombre,
        }

    except Exception as e:
        return {"error": f"Error en {nombre}: {str(e)}", "resultados": []}


def buscar_en_ahumada(producto: str) -> dict:
    q = producto.replace(" ", "%20")
    return _buscar_farmacia_playwright(
        producto, "Farmacia Ahumada",
        f"https://www.farmaciasahumada.cl/buscar?query={q}",
        ".product-name, .item-name, h2.name",
        ".price, .product-price, .normal-price"
    )


def buscar_en_salcobrand(producto: str) -> dict:
    q = producto.replace(" ", "%20")
    return _buscar_farmacia_playwright(
        producto, "Salcobrand",
        f"https://salcobrand.cl/search?term={q}",
        ".product-name, .pdp-name, h3.name",
        ".price, .product-price, span.price"
    )


def buscar_en_drsimi(producto: str) -> dict:
    q = producto.replace(" ", "%20")
    return _buscar_farmacia_playwright(
        producto, "Dr. Simi",
        f"https://www.drogueriasimi.cl/search?q={q}",
        ".product-name, .item-title, h2",
        ".price, .product-price, .offer-price"
    )


def buscar_en_cruzverde(producto: str) -> dict:
    q = producto.replace(" ", "%20")
    return _buscar_farmacia_playwright(
        producto, "Cruz Verde",
        f"https://www.cruzverde.cl/search?query={q}",
        ".product-name, .item-name, h2.name",
        ".price, .product-price, .normal-price"
    )
