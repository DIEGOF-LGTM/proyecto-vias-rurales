import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import database  # Módulo de SQLite/MySQL para la base de datos

app = Flask(__name__)

# Configuración de la carpeta para guardar las fotos subidas
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear la carpeta de uploads si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inicializar la base de datos al arrancar la aplicación
database.init_db()

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/guardar_reporte', methods=['POST'])
def guardar_reporte():
    if request.method == 'POST':
        vereda = request.form.get('vereda', '')
        estado = request.form.get('estado', 'Bueno')
        dano = request.form.get('dano', 'Ninguno')
        descripcion = request.form.get('descripcion', '')
        lat = request.form.get('lat', 0)
        lng = request.form.get('lng', 0)
        
        # Procesar la imagen subida
        foto_filename = 'sin_foto.jpg'
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and archivo_permitido(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto_filename = filename

        # Lógica o llamada al módulo de IA para evaluar la foto o descripción
        analisis_ia = f"Evaluación IA: Severidad {estado}"

        # Guardar en la base de datos (ajusta los parámetros según la función en database.py)
        database.insertar_reporte(vereda, estado, dano, descripcion, lat, lng, foto_filename, analisis_ia)

        return redirect(url_for('ver_reportes'))

@app.route('/reportes')
def ver_reportes():
    # Obtener todos los registros desde la base de datos
    datos = database.obtener_reportes()

    # Formatear los registros para pasarlos de forma segura al mapa y lista
    reportes_lista = []
    for r in datos:
        reportes_lista.append({
            "id": r[0],
            "vereda": r[1] if len(r) > 1 and r[1] else 'Sin vereda',
            "estado": r[2] if len(r) > 2 and r[2] else 'N/A',
            "dano": r[3] if len(r) > 3 and r[3] else 'N/A',
            "descripcion": r[4] if len(r) > 4 and r[4] else 'Sin descripción',
            "lat": r[5] if len(r) > 5 and r[5] else 0,
            "lng": r[6] if len(r) > 6 and r[6] else 0,
            "fecha": r[7] if len(r) > 7 and r[7] else '',
            "foto": r[8] if len(r) > 8 and r[8] else 'sin_foto.jpg',
            "ia": r[9] if len(r) > 9 and r[9] else 'Sin análisis'
        })

    return render_template('reportes.html', reportes=datos, reportes_json=reportes_lista)

if __name__ == '__main__':
    app.run(debug=True)