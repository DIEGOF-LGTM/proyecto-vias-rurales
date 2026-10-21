import os
import math
import uuid
import datetime
from functools import wraps

import requests
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash)
from werkzeug.security import check_password_hash

import database
from veredas import VEREDAS, CENTRO

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
UPLOADS = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

EXTENSIONES = {"jpg", "jpeg", "png", "webp"}
DANOS = ["Hueco / Bache profundo", "Derrumbe / Deslizamiento", "Inundación", "Drenaje",
         "Vía cerrada", "Vía bloqueada", "Otro"]
# Estos tipos NO son "daños" que sumen tiempo: son tramos que la ruta debe evitar.
CIERRES = ("Vía cerrada", "Vía bloqueada")
RADIO_CIERRE_M = 80  # radio alrededor del punto reportado que la ruta no debe tocar
ESTADOS = ["Bueno", "Regular", "Malo"]

# OpenRouteService (gratis, requiere clave): permite rodear zonas cerradas de verdad.
# Se configura en Render > Environment > ORS_API_KEY. Sin clave, se usa OSRM y solo
# se descartan las alternativas que pasan por el cierre.
ORS_KEY = os.environ.get("ORS_API_KEY")
ORS_PERFIL = {"car": "driving-car", "foot": "foot-walking", "bike": "cycling-regular"}

# Medios de transporte. "kmh" = velocidad media supuesta en vías rurales;
# "factor" = multiplica el tiempo de carro. "seg_dano" = segundos extra por cada daño cerca de la ruta.
# Son supuestos propios: justifícalos en el informe o ajústalos aquí.
MODOS = {
    "caminando": {"nombre": "Caminando", "icono": "🚶", "perfil": "foot", "kmh": 5,   "seg_dano": 30},
    "caballo":   {"nombre": "A caballo", "icono": "🐎", "perfil": "foot", "kmh": 7,   "seg_dano": 40},
    "bicicleta": {"nombre": "Bicicleta", "icono": "🚲", "perfil": "bike", "kmh": 12,  "seg_dano": 60},
    "moto":      {"nombre": "Moto",      "icono": "🏍️", "perfil": "car",  "factor": 0.9, "seg_dano": 120},
    "bus":       {"nombre": "Bus",       "icono": "🚌", "perfil": "car",  "factor": 1.4, "seg_dano": 150},
    "carro":     {"nombre": "Carro",     "icono": "🚗", "perfil": "car",  "factor": 1.0, "seg_dano": 120},
}
MEDIOS = [m["nombre"] for m in MODOS.values()] + ["Otro", "No indicado"]
SERVIDORES = {
    "car": "https://router.project-osrm.org/route/v1/driving",
    "foot": "https://routing.openstreetmap.de/routed-foot/route/v1/driving",
    "bike": "https://routing.openstreetmap.de/routed-bike/route/v1/driving",
}
TZ = datetime.timezone(datetime.timedelta(hours=-5))  # Colombia

database.init_db()


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def evaluar_foto(path):
    """Heurística con OpenCV: más bordes/textura = más daño visible."""
    try:
        import cv2
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return "No analizado"
        bordes = cv2.Canny(img, 80, 160).mean() / 255
        sev = "Malo" if bordes > 0.12 else "Regular" if bordes > 0.05 else "Bueno"
        return f"Evaluación IA: Severidad {sev}"
    except Exception:
        return "No analizado"


def dist_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(a))


def circulo(lat, lon, r=RADIO_CIERRE_M, n=16):
    """Polígono GeoJSON (lista de anillos) que aproxima un círculo de r metros."""
    dlat = r / 111320
    dlon = r / (111320 * math.cos(math.radians(lat)))
    anillo = [[lon + dlon * math.cos(2 * math.pi * i / n),
               lat + dlat * math.sin(2 * math.pi * i / n)] for i in range(n)]
    anillo.append(anillo[0])
    return [anillo]


def cruza_cierre(coords, cierres):
    """True si algún punto de la ruta ([lon, lat]) queda dentro del radio de un cierre."""
    return any(dist_m(la, lo, c[1], c[0]) < RADIO_CIERRE_M
               for la, lo in cierres for c in coords)


@app.errorhandler(413)
def muy_grande(_):
    flash("La foto pesa más de 8 MB. Sube una más liviana.")
    return redirect(url_for("index"))


@app.route("/")
def index():
    return render_template("index.html", veredas=VEREDAS, centro=CENTRO,
                           danos=DANOS, estados=ESTADOS, medios=MEDIOS)


@app.route("/reportar", methods=["POST"])
def reportar():
    f = request.form
    try:
        lat, lon = float(f["latitud"]), float(f["longitud"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError
    except (KeyError, ValueError):
        flash("Marca el punto del daño en el mapa.")
        return redirect(url_for("index"))

    via = f.get("via", "")
    if via == "__otra__":
        via = f.get("via_otra", "").strip()
    via = via[:80] or "Sin vereda"
    dano = f.get("dano") if f.get("dano") in DANOS else "Otro"
    estado = f.get("estado") if f.get("estado") in ESTADOS else "Regular"

    medio = f.get("medio") if f.get("medio") in MEDIOS else "No indicado"
    foto, ia = "sin_foto.jpg", "No analizado"
    archivo = request.files.get("foto")
    if archivo and archivo.filename:
        ext = archivo.filename.rsplit(".", 1)[-1].lower()
        if ext not in EXTENSIONES:
            flash("La foto debe ser JPG, PNG o WEBP.")
            return redirect(url_for("index"))
        foto = f"{uuid.uuid4().hex}.{ext}"
        ruta = os.path.join(UPLOADS, foto)
        archivo.save(ruta)
        ia = evaluar_foto(ruta)

    database.guardar_reporte(
        via, estado, dano, f.get("descripcion", "")[:500], lat, lon,
        datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M"), foto, ia, medio)
    flash("Reporte guardado.")
    return redirect(url_for("mapa"))


@app.route("/mapa")
def mapa():
    return render_template("mapa.html", veredas=VEREDAS, centro=CENTRO, modos=MODOS)


@app.route("/reportes")
def reportes():
    return render_template("reportes.html", reportes=database.obtener_reportes())


@app.route("/api/reportes")
def api_reportes():
    keys = ["id", "via", "estado", "dano", "descripcion", "lat", "lon",
            "fecha", "foto", "ia", "medio"]
    return jsonify([dict(zip(keys, r)) for r in database.obtener_reportes()])


def pedir_ruta_ors(perfil, olon, olat, dlon, dlat, cierres):
    """Ruta que rodea los cierres (OpenRouteService). Devuelve el mismo formato que OSRM."""
    body = {"coordinates": [[olon, olat], [dlon, dlat]],
            "options": {"avoid_polygons": {
                "type": "MultiPolygon",
                "coordinates": [circulo(la, lo) for la, lo in cierres]}}}
    try:
        r = requests.post(
            f"https://api.openrouteservice.org/v2/directions/{ORS_PERFIL[perfil]}/geojson",
            json=body, headers={"Authorization": ORS_KEY}, timeout=15)
        if r.status_code != 200:
            return None
        f = r.json()["features"][0]
        s = f["properties"]["summary"]
        return {"ors": True, "routes": [{"geometry": f["geometry"],
                                         "distance": s["distance"],
                                         "duration": s["duration"]}]}
    except Exception:
        return None


def pedir_ruta(perfil, olon, olat, dlon, dlat, cierres=()):
    if cierres and ORS_KEY:
        data = pedir_ruta_ors(perfil, olon, olat, dlon, dlat, cierres)
        if data:
            return data
    try:
        data = requests.get(
            f"{SERVIDORES[perfil]}/{olon},{olat};{dlon},{dlat}",
            params={"overview": "full", "geometries": "geojson", "alternatives": "true"},
            headers={"User-Agent": "MiVia/1.0 (proyecto academico)"},
            timeout=10).json()
        return data if data.get("code") == "Ok" else None
    except Exception:
        return None


@app.route("/api/ruta")
def api_ruta():
    try:
        olat, olon = float(request.args["olat"]), float(request.args["olon"])
        dlat, dlon = float(request.args["dlat"]), float(request.args["dlon"])
    except (KeyError, ValueError):
        return jsonify({"error": "Faltan coordenadas"}), 400
    cfg = MODOS.get(request.args.get("modo", "carro"), MODOS["carro"])

    todos = database.obtener_reportes()
    # columnas: 0 id, 1 via, 2 estado, 3 dano, 4 descripcion, 5 lat, 6 lon, ...
    cierres = [(r[5], r[6]) for r in todos if r[3] in CIERRES]
    reps = [(r[5], r[6], r[3]) for r in todos if r[3] not in CIERRES]

    data = pedir_ruta(cfg["perfil"], olon, olat, dlon, dlat, cierres)
    aproximada = False
    if data is None and cfg["perfil"] != "car":      # plan B: usar la red de carreteras
        data = pedir_ruta("car", olon, olat, dlon, dlat, cierres)
        aproximada = data is not None
    if data is None:
        return jsonify({"error": "No hay ruta entre esos puntos o el servicio no responde. Intenta de nuevo."}), 502

    rutas = []
    for rt in data.get("routes", []):
        coords = rt["geometry"]["coordinates"]  # [lon, lat]
        # OSRM no sabe evitar zonas: descartamos las alternativas que pasan por un cierre.
        # (Las de OpenRouteService ya vienen rodeándolos.)
        if cierres and not data.get("ors") and cruza_cierre(coords, cierres):
            continue
        muestra = coords[::4] or coords
        cerca = [{"lat": la, "lon": lo, "dano": d} for la, lo, d in reps
                 if any(dist_m(la, lo, c[1], c[0]) < 60 for c in muestra)]
        km = rt["distance"] / 1000
        seg = km / cfg["kmh"] * 3600 if "kmh" in cfg else rt["duration"] * cfg["factor"]
        rutas.append({
            "geometry": rt["geometry"],
            "distancia_km": round(km, 1),
            "tiempo_min": max(1, round(seg / 60)),
            "tiempo_ajustado_min": max(1, round((seg + len(cerca) * cfg["seg_dano"]) / 60)),
            "afectaciones": cerca,
        })
    if not rutas:
        return jsonify({"error": "Todas las rutas posibles pasan por una vía cerrada o bloqueada reportada."}), 404
    rutas.sort(key=lambda x: x["tiempo_ajustado_min"])
    return jsonify({"rutas": rutas, "modo": cfg["nombre"], "seg_dano": cfg["seg_dano"],
                    "aproximada": aproximada, "cierres": len(cierres)})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        h = database.obtener_hash(request.form.get("usuario", ""))
        if h and check_password_hash(h, request.form.get("password", "")):
            session["admin"] = True
            return redirect(url_for("reportes"))
        flash("Usuario o contraseña incorrectos.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/borrar/<int:id_>", methods=["POST"])
@admin_required
def borrar(id_):
    database.borrar_reporte(id_)
    flash("Reporte eliminado.")
    return redirect(url_for("reportes"))


if __name__ == "__main__":
    app.run(debug=True)