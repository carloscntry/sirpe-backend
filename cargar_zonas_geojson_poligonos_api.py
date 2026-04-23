import json
import re
import requests

API_URL = "http://127.0.0.1:8000/zonas/"
ARCHIVO_GEOJSON = "vf 204 vectores - 10 Zonas 2026.geojson"

# Campos posibles donde puede venir el nombre de la zona
CAMPOS_NOMBRE = [
    "nombre", "NOMBRE",
    "zona", "ZONA",
    "name", "Name",
    "nom", "NOM",
    "descripcion", "DESCRIPCION", "Descripción", "DESCRIPCIÓN",
    "label", "LABEL",
    "id", "ID",
    "cve", "CVE",
    "clave", "CLAVE"
]


def calcular_centroide_simple(coordinates):
    """
    Calcula un centroide aproximado usando el primer anillo.
    GeoJSON usa [longitud, latitud].
    """
    if not coordinates or not coordinates[0]:
        return None, None

    puntos = coordinates[0]
    suma_lon = 0
    suma_lat = 0
    total = 0

    for punto in puntos:
        if len(punto) < 2:
            continue
        lon, lat = punto[0], punto[1]
        suma_lon += lon
        suma_lat += lat
        total += 1

    if total == 0:
        return None, None

    return suma_lat / total, suma_lon / total


def normalizar_texto(texto):
    if texto is None:
        return ""
    texto = str(texto).strip().upper()
    texto = texto.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def extraer_nombre_desde_properties(properties):
    """
    Busca el nombre en múltiples campos.
    """
    for campo in CAMPOS_NOMBRE:
        valor = properties.get(campo)
        if valor is not None and str(valor).strip():
            return str(valor).strip()

    # Como respaldo, revisa todos los values tipo texto
    for _, valor in properties.items():
        if isinstance(valor, str) and valor.strip():
            return valor.strip()

    return ""


def homologar_a_zona_principal(nombre_original):
    """
    Convierte distintos formatos a:
    ZONA 1 ... ZONA 10, ZONA CH
    Si no corresponde a una zona principal, devuelve None.
    """
    nombre = normalizar_texto(nombre_original)

    # Centro Histórico
    if nombre in {
        "CH",
        "ZONA CH",
        "CENTRO HISTORICO",
        "CENTRO HISTORICO CH",
        "ZONA CENTRO HISTORICO"
    }:
        return "ZONA CH"

    # Coincidencias como ZONA 1, ZONA 10, ZONA-10, ZONA10
    match_zona = re.search(r"\bZONA[\s\-]*([0-9]{1,2})\b", nombre)
    if match_zona:
        numero = int(match_zona.group(1))
        if 1 <= numero <= 10:
            return f"ZONA {numero}"

    # Coincidencias donde solo venga el número
    if re.fullmatch(r"[0-9]{1,2}", nombre):
        numero = int(nombre)
        if 1 <= numero <= 10:
            return f"ZONA {numero}"

    # Coincidencias tipo "10A ZONA", "AREA 10", etc. solo si trae 1..10 aislado
    match_numero = re.search(r"\b([0-9]{1,2})\b", nombre)
    if match_numero:
        numero = int(match_numero.group(1))
        if 1 <= numero <= 10 and ("ZONA" in nombre or "AREA" in nombre or "SECTOR" in nombre):
            return f"ZONA {numero}"

    return None


def obtener_geometry_y_centroide(geometry):
    geo_type = geometry.get("type")

    if geo_type == "Polygon":
        coordinates = geometry.get("coordinates", [])
        if not coordinates:
            return None, None, None
        latitud, longitud = calcular_centroide_simple(coordinates)
        return geometry, latitud, longitud

    if geo_type == "MultiPolygon":
        multipolygon = geometry.get("coordinates", [])
        if not multipolygon or not multipolygon[0]:
            return None, None, None

        # Se conserva el MultiPolygon completo, pero el centroide se estima con el primer polígono
        coordinates = multipolygon[0]
        latitud, longitud = calcular_centroide_simple(coordinates)
        return geometry, latitud, longitud

    return None, None, None


def main():
    with open(ARCHIVO_GEOJSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    print(f"Se encontraron {len(features)} elementos en el GeoJSON")

    zonas_detectadas = {}
    omitidas = 0

    for i, feature in enumerate(features, start=1):
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})

        if not geometry:
            print(f"[OMITIDA] Feature {i} sin geometry")
            omitidas += 1
            continue

        nombre_crudo = extraer_nombre_desde_properties(properties)
        nombre_homologado = homologar_a_zona_principal(nombre_crudo)

        print(f"[DEBUG] Feature {i}: '{nombre_crudo}' -> '{nombre_homologado}'")

        if not nombre_homologado:
            omitidas += 1
            continue

        geometry_final, latitud, longitud = obtener_geometry_y_centroide(geometry)
        if geometry_final is None or latitud is None or longitud is None:
            print(f"[OMITIDA] {nombre_crudo} geometry inválida o no soportada")
            omitidas += 1
            continue

        # Evitar duplicados: si vuelve a aparecer la misma zona principal, se conserva la primera
        if nombre_homologado in zonas_detectadas:
            print(f"[DUPLICADA] {nombre_homologado} ya detectada, se omite repetida")
            continue

        zonas_detectadas[nombre_homologado] = {
            "nombre": nombre_homologado,
            "tipo": "operativa",
            "nivel_riesgo": "Medio",
            "latitud": latitud,
            "longitud": longitud,
            "geometry_geojson": json.dumps(geometry_final, ensure_ascii=False)
        }

    print("\nZonas principales detectadas:")
    for nombre in sorted(zonas_detectadas.keys()):
        print(f" - {nombre}")

    esperadas = {f"ZONA {i}" for i in range(1, 11)}
    esperadas.add("ZONA CH")

    faltantes = esperadas - set(zonas_detectadas.keys())
    if faltantes:
        print("\n[ADVERTENCIA] Faltan zonas por detectar:")
        for nombre in sorted(faltantes):
            print(f" - {nombre}")

    print(f"\nTotal detectadas para cargar: {len(zonas_detectadas)}")

    # Cargar a la API
    cargadas = 0
    for nombre in sorted(zonas_detectadas.keys(), key=lambda x: (x != "ZONA CH", x)):
        payload = zonas_detectadas[nombre]

        try:
            response = requests.post(API_URL, json=payload, timeout=20)
            if response.status_code in (200, 201):
                print(f"[OK] Zona cargada: {nombre}")
                cargadas += 1
            else:
                print(f"[ERROR] {nombre}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[ERROR] Excepción al cargar {nombre}: {e}")

    print(f"\nTotal cargadas: {cargadas}")
    print(f"Total omitidas durante análisis: {omitidas}")


if __name__ == "__main__":
    main()