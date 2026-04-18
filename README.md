# 🛒 Agente Comparador de Precios

Agente de IA en Python que busca y compara precios de productos en múltiples tiendas usando Claude como cerebro.

## Estructura del proyecto

```
comparador-precios/
├── main.py      ← Punto de entrada. Ejecuta este archivo
├── agent.py     ← Cerebro del agente (lógica con Claude)
├── tools.py     ← Herramientas de búsqueda de precios
└── README.md    ← Este archivo
```

## Configuración inicial

### 1. Activar el entorno virtual
```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 2. Configurar tu clave de Anthropic
```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui

# Mac / Linux
export ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
```

### 3. (Opcional) Agregar clave de SerpApi para precios reales
Sin clave SerpApi el agente funciona en **modo demo** con datos de ejemplo.
Para precios reales:
1. Regístrate gratis en https://serpapi.com (100 búsquedas/mes gratis)
2. Copia tu API key
3. Ábrela en `tools.py` y reemplaza `TU_CLAVE_SERPAPI_AQUI` con tu clave

## Cómo ejecutar

### Modo interactivo (recomendado)
```bash
python main.py
```
El agente te pedirá productos uno a uno.

### Modo directo
```bash
python main.py "Samsung Galaxy S24 256GB"
python main.py "zapatillas Nike Air Max talla 42"
python main.py "notebook Lenovo IdeaPad"
```

## Ejemplo de salida

```
=======================================================
🔍 Buscando precios para: iPhone 15 128GB

🔧 Usando herramienta: buscar_en_google_shopping
   └─ Buscando: iPhone 15 128GB
   └─ 8 resultados encontrados en Google Shopping

🔧 Usando herramienta: buscar_en_falabella
   └─ Buscando: iPhone 15 128GB
   └─ 4 resultados encontrados en Falabella Chile

🔧 Usando herramienta: comparar_precios
   └─ Comparando 12 ofertas encontradas

-------------------------------------------------------
✅ Análisis completado

🏆 Mejor precio: $749.990 en TechStore

📊 Ranking de precios:
1. TechStore          $749.990  ✅ Envío gratis
2. Falabella          $779.990  📦 Envío $3.990
3. Paris              $799.990  📦 Envío gratis
4. Ripley             $819.990  📦 Envío $5.990

💰 Ahorro potencial: $70.000 comprando en TechStore vs Ripley

💡 Consejos:
- TechStore tiene la mejor relación precio/envío
- Falabella tiene cuotas sin interés con tarjeta CMR
```

## Cómo extender el agente

### Agregar una nueva tienda
En `tools.py`, crea una nueva función siguiendo el mismo patrón:

```python
def buscar_en_nueva_tienda(producto: str) -> dict:
    # Tu código aquí
    return {
        "producto_buscado": producto,
        "total_resultados": len(resultados),
        "resultados": resultados,
        "fuente": "Nombre Tienda",
    }
```

Luego agrégala en `agent.py`:
- En la lista `HERRAMIENTAS` (descripción para Claude)
- En el diccionario `MAPA_FUNCIONES` (referencia a la función)

## Tecnologías usadas

- **anthropic** — SDK de Claude para Python
- **requests** — Hacer solicitudes HTTP a tiendas
- **beautifulsoup4** — Extraer datos de páginas web
- **serpapi** — API de Google Shopping (opcional)
