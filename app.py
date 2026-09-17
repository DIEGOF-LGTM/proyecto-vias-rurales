from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from database import init_db, guardar_reporte, obtener_reportes, eliminar_reporte
from datetime import date
from werkzeug.security import check_password_hash
import folium
import os

app = Flask(__name__)
# SECRET_KEY es obligatorio para que las sesiones (login) funcionen.
# En Render, configúrala como variable de entorno; el valor por defecto
# de aquí es solo para pruebas locales, NO la dejes así en producción.
app.secret_key = os.environ.get("SECRET_KEY", "clave-temporal-solo-para-desarrollo-local")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
# La contraseña NUNCA se guarda en texto plano (cumple RNF-07).
# ADMIN_PASSWORD_HASH se genera una vez y se pega como variable de entorno en Render.
# Ver instrucciones para generarla al final de este archivo.
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

# Control para que si la base de datos falla al iniciar, el servidor no colapse en Render
try:
    init_db()
    print("Base de datos inicializada correctamente.")
except Exception as e:
    print(f"Advertencia: No se pudo conectar a la base de datos al arrancar: {e}")


def admin_requerido(f):
    """Decorador que bloquea el acceso a una ruta si no hay sesión de
    administrador activa. Cumple RF-06 y RNF-06."""
    @wraps(f)
    def decorador(*args, **kwargs):
        if not session.get("es_admin"):
            flash("Debes iniciar sesión como administrador para hacer eso.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorador


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
    # Le pasamos es_admin a la plantilla para que solo muestre el botón
    # de eliminar cuando hay sesión activa (ajustar reportes.html, ver nota abajo).
    return render_template("reportes.html", reportes=datos, es_admin=session.get("es_admin", False))


@app.route("/eliminar/<int:id>")
@admin_requerido
def eliminar(id):
    try:
        eliminar_reporte(id)
    except Exception as e:
        print(f"Error al eliminar reporte: {e}")
    return redirect(url_for("reportes"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        clave = request.form.get("clave", "")

        if usuario == ADMIN_USER and ADMIN_PASSWORD_HASH and check_password_hash(ADMIN_PASSWORD_HASH, clave):
            session["es_admin"] = True
            return redirect(url_for("reportes"))
        error = "Usuario o contraseña incorrectos."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("es_admin", None)
    return redirect(url_for("index"))


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
    port = int(os.environ.get("PORT", 5000))
    # debug ya NO queda encendido por defecto en producción (antes estaba
    # fijo en True, lo cual expone trazas de error a cualquiera en Render).
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)