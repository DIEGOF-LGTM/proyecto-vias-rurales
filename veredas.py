# Formato:  "Nombre": (latitud, longitud)
# None = todavía sin coordenadas. La vereda aparece igual en las listas y el mapa
# intenta ubicarla solo (búsqueda en OpenStreetMap). Para fijar la coordenada exacta:
#   1) abre  /mapa?calibrar=1
#   2) elige la vereda en "Ir a vereda…"
#   3) haz clic sobre el mapa donde está y copia la línea que sale
#   4) pégala aquí reemplazando el None
#
# Las nueve veredas (según Wikipedia y FamilySearch) más los nombres locales que
# usa la gente al reportar. Verifica la lista contra el EOT de la alcaldía.
VEREDAS = {
    "Soaga": (5.3250, -73.8140),
    "Volcán": None,
    "Palo Gordo": None,
    "Guatancuy": None,
    "Centro del Llano": None,
    "Sucunchoque": None,
    "Tausavita": None,
    "La Patera": None,
    "Apartadero": None,
    # Nombres locales (parecen sectores dentro de una vereda, no veredas aparte):
    "Chirquín": None,      # sector de Guatancuy
    "El Cedro": None,      # sector de Volcán (Volcán No. 3)
    "Getsemaní": None,     # no lo encontré en fuentes: confirma dónde queda
}
CENTRO = (5.3085, -73.8161)  # Ubaté