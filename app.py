from flask import Flask, render_template, request, redirect, url_for
from database import init_db, guardar_reporte, obtener_reportes, eliminar_reporte
from datetime import date
import folium
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    mensaje = None
    if request.method == "POST":
        via = request.form["via"]
        estado = request.form["estado"]
        dano = request.form["dano"]
        descripcion = request.form["descripcion"]
        latitud = request.form["latitud"]
        longitud = request.form["longitud"]
        fecha = str(date.today())

        try:
            latitud = float(latitud)
            longitud = float(longitud)
            guardar_reporte(via, estado, dano, descripcion, latitud, longitud, fecha)
            mensaje = "✅ Reporte guardado correctamente."
        except ValueError:
            mensaje = "❌ Latitud y longitud deben ser números."

    return render_template("index.html", mensaje=mensaje)

@app.route("/reportes")
def reportes():
    datos = obtener_reportes()
    return render_template("reportes.html", reportes=datos)

@app.route("/eliminar/<int:id>")
def eliminar(id):
    eliminar_reporte(id)
    return redirect(url_for("reportes"))

@app.route("/mapa")
def mapa():
    datos = obtener_reportes()
    m = folium.Map(location=[5.3147, -73.8185], zoom_start=12)

    colores = {
        "Hueco": "red",
        "Derrumbe": "orange",
        "Inundación": "blue",
        "Otro": "gray"
    }

    for r in datos:
        id_, via, estado, dano, descripcion, lat, lon, fecha = r
        color = colores.get(dano, "gray")
        popup_text = f"<b>{via}</b><br>Daño: {dano}<br>Estado: {estado}<br>Fecha: {fecha}<br>{descripcion}"
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=250),
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    mapa_path = os.path.join("static", "mapa_generado.html")
    m.save(mapa_path)
    return render_template("mapa.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
    