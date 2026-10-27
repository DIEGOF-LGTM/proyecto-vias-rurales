/* Marcadores de reportes: icono y color por tipo de daño, popup al pasar el mouse
   (o al tocar en el celular) y filtros por tipo. Lo usan index.html y mapa.html.
   Necesita Leaflet y las funciones esc() y $() de base.html. */

const CIERRE = ['Vía cerrada', 'Vía bloqueada'];   // las rutas evitan estos puntos
const RADIO_CIERRE = 80;                           // metros; debe coincidir con RADIO_CIERRE_M de app.py

// forma: 'redondo' = daño que se puede cruzar; 'cuadrado' = cierre (señal de tránsito)
const TIPOS = {
  'Hueco / Bache profundo': {corto: 'Hueco', color: '#ef4444', forma: 'redondo',
    svg: '<path d="M2.5 10h5.5l2 8.5h4l2-8.5h5.5"/><path d="M5 21h14"/><circle cx="10" cy="5.8" r="1.2" fill="#fff" stroke="none"/><circle cx="14.2" cy="5" r="1" fill="#fff" stroke="none"/>'},
  'Derrumbe / Deslizamiento': {corto: 'Derrumbe', color: '#a16207', forma: 'redondo',
    svg: '<path d="M2.5 20.5l7-12 4.5 7 2.5-3.5 5 8.5z"/><circle cx="16.5" cy="4.8" r="1.5" fill="#fff" stroke="none"/><circle cx="20" cy="8.3" r="1.1" fill="#fff" stroke="none"/><circle cx="13" cy="4.3" r="1" fill="#fff" stroke="none"/>'},
  'Inundación': {corto: 'Inundación', color: '#2563eb', forma: 'redondo',
    svg: '<path d="M2.5 8.5c1.6-2 3.2-2 4.8 0s3.2 2 4.8 0 3.2-2 4.8 0 3.2 2 4.8 0"/><path d="M2.5 13.5c1.6-2 3.2-2 4.8 0s3.2 2 4.8 0 3.2-2 4.8 0 3.2 2 4.8 0"/><path d="M2.5 18.5c1.6-2 3.2-2 4.8 0s3.2 2 4.8 0 3.2-2 4.8 0 3.2 2 4.8 0"/>'},
  'Drenaje': {corto: 'Drenaje', color: '#7c3aed', forma: 'redondo',
    svg: '<rect x="4" y="5" width="16" height="14" rx="2.5"/><path d="M9.3 8.5v7M12 8.5v7M14.7 8.5v7"/>'},
  'Vía cerrada': {corto: 'Vía cerrada', color: '#7f1d1d', forma: 'cuadrado',
    svg: '<circle cx="12" cy="12" r="8.5"/><path d="M7 12h10" stroke-width="3.2"/>'},
  'Vía bloqueada': {corto: 'Bloqueada', color: '#ea580c', forma: 'cuadrado',
    svg: '<path d="M3 7.5h18v5.5H3z"/><path d="M8 7.5l-2.5 5.5M13.5 7.5L11 13M19 7.5L16.5 13"/><path d="M6 13v6.5M18 13v6.5"/>'},
  'Otro': {corto: 'Otro', color: '#6b7280', forma: 'redondo',
    svg: '<path d="M12 3.5l9.5 16.5h-19z"/><path d="M12 10v4.5"/><circle cx="12" cy="17.2" r="1.1" fill="#fff" stroke="none"/>'}
};
const ESTADO_COLOR = {'Bueno': '#22c55e', 'Regular': '#eab308', 'Malo': '#ef4444'};

const claveTipo = d => TIPOS[d] ? d : 'Otro';
const svgIcono = t => '<svg viewBox="0 0 24 24" aria-hidden="true">' + t.svg + '</svg>';

// Marcador: figura de color con el icono del daño, punta hacia el punto y un puntito del estado
function iconoDano(k, estado){
  const t = TIPOS[k];
  return L.divIcon({
    className: '', iconSize: [40, 48], iconAnchor: [20, 47], popupAnchor: [0, -44],
    html: '<div class="mk ' + t.forma + '" style="--c:' + t.color + '">'
        + '<i class="pt"></i><div class="fig">' + svgIcono(t) + '</div>'
        + '<i class="est" style="--c:' + (ESTADO_COLOR[estado] || '#9ca3af') + '"></i></div>'
  });
}

function popupReporte(r, k){
  const t = TIPOS[k];
  const foto = r.foto && r.foto !== 'sin_foto.jpg'
    ? '<img class="pp-foto" src="/static/uploads/' + encodeURIComponent(r.foto) + '" alt="Foto del reporte" loading="lazy">' : '';
  const ia = r.ia && r.ia !== 'No analizado' ? '<p class="pp-ia">🤖 ' + esc(r.ia) + '</p>' : '';
  const desc = r.descripcion ? '<p>' + esc(r.descripcion) + '</p>' : '';
  const medio = r.medio && r.medio !== 'No indicado' ? '<p class="pp-sub">Iba: ' + esc(r.medio) + '</p>' : '';
  return '<div class="pp">'
    + '<div class="pp-cab" style="--c:' + t.color + '"><span class="sw ' + t.forma + '">' + svgIcono(t) + '</span><b>' + esc(r.dano) + '</b></div>'
    + '<div class="pp-sub">' + esc(r.via) + ' · <span class="sdot" style="--c:' + (ESTADO_COLOR[r.estado] || '#9ca3af') + '"></span>' + esc(r.estado) + '</div>'
    + desc + medio + ia + foto
    + '<div class="pp-pie"><small>' + esc(r.fecha) + '</small><a href="/reporte/' + Number(r.id) + '">💬 ' + Number(r.n) + ' aporte(s) · Ver y comentar</a></div></div>';
}

// El popup se abre al pasar el mouse (o al tocar en el celular) y se cierra al salir,
// con una pequeña espera para poder entrar al popup y usar el enlace.
function abrirAlPasar(marker, html, mapa){
  const pop = L.popup({autoPan: false, maxWidth: 270, minWidth: 220, offset: [0, 0], className: 'pp-wrap'});
  let t;
  const abrir = () => {
    clearTimeout(t);
    if (mapa.hasLayer(pop)) return;
    pop.setLatLng(marker.getLatLng()).setContent(html).openOn(mapa);
    const el = pop.getElement();
    if (el) {
      el.addEventListener('mouseenter', () => clearTimeout(t));
      el.addEventListener('mouseleave', cerrar);
    }
  };
  const cerrar = () => { clearTimeout(t); t = setTimeout(() => mapa.closePopup(pop), 350); };
  marker.on('mouseover click', abrir);
  marker.on('mouseout', cerrar);
  marker.on('remove', () => { clearTimeout(t); mapa.closePopup(pop); });
}

// Dibuja todos los reportes agrupados por tipo. Devuelve los grupos para armar la leyenda.
function dibujarReportes(lista, mapa){
  const grupos = {};
  Object.keys(TIPOS).forEach(k => { grupos[k] = {capa: L.layerGroup().addTo(mapa), n: 0, activo: true}; });
  lista.forEach(r => {
    const k = claveTipo(r.dano), g = grupos[k];
    g.n++;
    if (CIERRE.includes(k))
      L.circle([r.lat, r.lon], {radius: RADIO_CIERRE, color: TIPOS[k].color, weight: 2, dashArray: '6 4', fillOpacity: .15, interactive: false}).addTo(g.capa);
    const m = L.marker([r.lat, r.lon], {icon: iconoDano(k, r.estado), title: r.dano, riseOnHover: true,
      zIndexOffset: CIERRE.includes(k) ? 500 : 0}).addTo(g.capa);
    abrirAlPasar(m, popupReporte(r, k), mapa);
  });
  return grupos;
}

// Leyenda con filtros: cada botón muestra u oculta los reportes de ese tipo
function leyenda(el, grupos, mapa){
  el.textContent = '';
  const fila = document.createElement('div');
  fila.className = 'chips-tipo';
  Object.keys(TIPOS).forEach(k => {
    const t = TIPOS[k], g = grupos[k];
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'chip-tipo'; b.setAttribute('aria-pressed', 'true');
    b.style.setProperty('--c', t.color);
    b.innerHTML = '<span class="sw ' + t.forma + '">' + svgIcono(t) + '</span>' + esc(t.corto) + ' <small>' + g.n + '</small>';
    b.onclick = () => {
      g.activo = !g.activo;
      if (g.activo) mapa.addLayer(g.capa); else mapa.removeLayer(g.capa);
      b.classList.toggle('off', !g.activo);
      b.setAttribute('aria-pressed', String(g.activo));
    };
    fila.appendChild(b);
  });
  el.appendChild(fila);
  const e = document.createElement('p');
  e.className = 'suave leyenda';
  e.innerHTML = 'Puntito de la esquina = estado de la vía: '
    + '<span class="sdot" style="--c:#22c55e"></span>Bueno '
    + '<span class="sdot" style="--c:#eab308"></span>Regular '
    + '<span class="sdot" style="--c:#ef4444"></span>Malo. '
    + 'Los cuadrados son cierres: las rutas los evitan. Toca un tipo para ocultarlo o mostrarlo.';
  el.appendChild(e);
}