import os
import math
import uuid
import datetime
from functools import wraps

import requests
from flask import (Flask, render_template, request, redirect, url_for,
                   session, jsonify, flash)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave")
UPLOADS = os.path.join(app.static_folder, "uploads")
os.makedirs(UPLOADS, exist_ok=True)
database.init_db()

# IMPORTANTE: pega aquí tus 9 veredas oficiales con sus coordenadas (lat, lon)
VEREDAS = {
    "Soaga": (5.3250, -73.8140),
    # "Otra vereda": (5.xxxx, -73.xxxx),
}
CENTRO = (5.3085, -73.8161)  # Ubaté
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
SEGUNDOS_POR_DANO = 120  # supuesto: cada daño cercano suma 2 min


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def evaluar_foto(path):
    """Heurística simple con OpenCV: más bordes/textura = más daño visible."""
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


@app.route("/")
def index():
    return render_template("index.html", veredas=VEREDAS, centro=CENTRO)


@app.route("/reportar", methods=["POST"])
def reportar():
    f = request.form
    try:
        lat, lon = float(f["latitud"]), float(f["longitud"])
    except (KeyError, ValueError):
        flash("Toca el mapa para marcar el punto del daño.")
        return redirect(url_for("index"))
    foto, ia = "sin_foto.jpg", "No analizado"
    archivo = request.files.get("foto")
    if archivo and archivo.filename:
        foto = f"{uuid.uuid4().hex}_{secure_filename(archivo.filename)}"
        ruta = os.path.join(UPLOADS, foto)
        archivo.save(ruta)
        ia = evaluar_foto(ruta)
    database.guardar_reporte(
        f.get("via", ""), f.get("estado", "Regular"), f.get("dano", "Otro"),
        f.get("descripcion", ""), lat, lon,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), foto, ia)
    flash("Reporte guardado.")
    return redirect(url_for("mapa"))


@app.route("/mapa")
def mapa():
    return render_template("mapa.html", centro=CENTRO)


@app.route("/reportes")
def reportes():
    return render_template("reportes.html", reportes=database.obtener_reportes())


@app.route("/api/reportes")
def api_reportes():
    keys = ["id", "via", "estado", "dano", "descripcion", "lat", "lon",
            "fecha", "foto", "ia"]
    return jsonify([dict(zip(keys, r)) for r in database.obtener_reportes()])


@app.route("/api/ruta")
def api_ruta():
    try:
        olat, olon = float(request.args["olat"]), float(request.args["olon"])
        dlat, dlon = float(request.args["dlat"]), float(request.args["dlon"])
    except (KeyError, ValueError):
        return jsonify({"error": "Faltan coordenadas"}), 400
    try:
        data = requests.get(
            f"{OSRM_URL}/{olon},{olat};{dlon},{dlat}",
            params={"overview": "full", "geometries": "geojson", "alternatives": "true"},
            timeout=10).json()
    except Exception:
        return jsonify({"error": "No se pudo calcular la ruta"}), 502
    reps = [(r[5], r[6], r[3]) for r in database.obtener_reportes()]
    rutas = []
    for rt in data.get("routes", []):
        coords = rt["geometry"]["coordinates"]
        muestra = coords[::5] or coords
        cerca = [{"lat": la, "lon": lo, "dano": d} for la, lo, d in reps
                 if any(dist_m(la, lo, c[1], c[0]) < 60 for c in muestra)]
        rutas.append({
            "geometry": rt["geometry"],
            "distancia_km": round(rt["distance"] / 1000, 1),
            "tiempo_min": round(rt["duration"] / 60),
            "tiempo_ajustado_min": round((rt["duration"] + len(cerca) * SEGUNDOS_POR_DANO) / 60),
            "afectaciones": cerca,
        })
    rutas.sort(key=lambda x: x["tiempo_ajustado_min"])
    return jsonify(rutas)


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
    return redirect(url_for("reportes"))


if __name__ == "__main__":
    app.run(debug=True)