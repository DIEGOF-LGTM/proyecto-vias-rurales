from flask import Flask, render_template, request, redirect, url_for
from database import init_db, guardar_reporte, obtener_reportes, eliminar_reporte
from datetime import date
import folium
import os

app = Flask(__name__)

# Control para que si la base de datos falla al iniciar, el servidor no colapse en Render
try:
    init_db()
    print("Base de datos inicializada correctamente.")
except Exception as e:
    print(f"Advertencia: No se pudo conectar a la base de datos al arrancar: {e}")

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
        except Exception as e:
            mensaje = f"❌ Error al guardar en la base de datos: {e}"

    return render_template("index.html", mensaje=mensaje)

@app.route("/reportes")
def reportes():
    try:
        datos = obtener_reportes()
    except Exception as e:
        print(f"Error al obtener reportes: {e}")
        datos = []
    return render_template("reportes.html", reportes=datos)

@app.route("/eliminar/<int:id>")
def eliminar(id):
    try:
        eliminar_reporte(id)
    except Exception as e:
        print(f"Error al eliminar reporte: {e}")
    return redirect(url_for("reportes"))

@app.route("/mapa")
def mapa():
    try:
        datos = obtener_reportes()
    except Exception as e:
        print(f"Error al obtener reportes para el mapa: {e}")
        datos = []

    m = folium.Map(location=[5.3147, -73.8185], zoom_start=12)

    colores = {
        "Hueco": "red",
        "Derrumbe": "orange",
        "Inundación": "blue",
        "Otro": "gray"
    }

    for r in datos:
        try:
            id_, via, estado, dano, descripcion, lat, lon, fecha = r
            color = colores.get(dano, "gray")
            popup_text = f"<b>{via}</b><br>Daño: {dano}<br>Estado: {estado}<br>Fecha: {fecha}<br>{descripcion}"
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_text, max_width=250),
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)
        except Exception as e:
            print(f"Error al procesar marcador: {e}")

    os.makedirs("static", exist_ok=True)
    mapa_path = os.path.join("static", "mapa_generado.html")
    m.save(mapa_path)
    return render_template("mapa.html")

if __name__ == "__main__":
    # Captura el puerto dinámico asignado por Render ($PORT) o usa 5000 en desarrollo local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)