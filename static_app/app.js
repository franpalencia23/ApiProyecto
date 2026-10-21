/* app.js - App movil "Estres Hidrico".
   Todo el acceso a datos pasa por la API (mismo origen): nunca toca la base directamente. */
(function () {
  'use strict';
  const G = window.Graficos;
  const API = '';                       // mismo origen que sirve la app (Render)
  const $ = (s, r) => (r || document).querySelector(s);

  const ESTADOS = {
    optimo:     { txt: 'Óptimo',     color: '#2e8b57', consejo: 'El suelo está en buenas condiciones. No requiere riego.' },
    precaucion: { txt: 'Precaución', color: '#c98f00', consejo: 'Humedad o temperatura al límite. Vigilar y planear riego pronto.' },
    estres:     { txt: 'Estrés',     color: '#dd6a0b', consejo: 'La planta sufre estrés hídrico. Regar hoy.' },
    critico:    { txt: 'Crítico',    color: '#c62828', consejo: 'Condición crítica. Riego urgente.' }
  };
  const ORDEN = ['optimo', 'precaucion', 'estres', 'critico'];

  // Mismos umbrales que los LEDs del ESP32 y la consulta SQL de distribucion
  function clasificar(t, h) {
    if (h < 15 || t > 40) return 'critico';
    if (h < 30 || t > 35) return 'estres';
    if (h < 50 || t > 28) return 'precaucion';
    return 'optimo';
  }

  const S = { token: null, rol: null, zonas: [], zona: '', tab: 'inicio' };
  try { S.token = localStorage.getItem('eh_token'); S.rol = localStorage.getItem('eh_rol'); } catch (e) {}

  /* ---------------- acceso a la API ---------------- */
  async function api(ruta, opciones) {
    opciones = opciones || {};
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 90000);   // Render gratis puede tardar ~50 s en despertar
    const cab = Object.assign({}, opciones.headers || {});
    if (S.token) cab['Authorization'] = 'Bearer ' + S.token;
    try {
      const r = await fetch(API + ruta, Object.assign({}, opciones, { headers: cab, signal: ctl.signal }));
      if (r.status === 401 && S.token) { cerrarSesion('Tu sesión expiró. Ingresa de nuevo.'); throw new Error('401'); }
      if (!r.ok) {
        let d = '';
        try { d = (await r.json()).detail || ''; } catch (e) {}
        throw new Error(d || ('Error ' + r.status));
      }
      return await r.json();
    } finally { clearTimeout(t); }
  }
  const est = (ruta, extra) => {
    const p = new URLSearchParams(extra || {});
    return api('/api/v1/estadisticas/' + ruta + (p.toString() ? '?' + p : ''));
  };
  const zq = () => (S.zona ? { id_zona: S.zona } : {});

  /* ---------------- sesion ---------------- */
  function mostrar(pantalla) {
    $('#login').hidden = pantalla !== 'login';
    $('#app').hidden = pantalla !== 'app';
  }
  function cerrarSesion(msg) {
    S.token = null; S.rol = null;
    try { localStorage.removeItem('eh_token'); localStorage.removeItem('eh_rol'); } catch (e) {}
    mostrar('login');
    const er = $('#login-error');
    if (msg) { er.textContent = msg; er.hidden = false; } else { er.hidden = true; }
  }

  $('#form-login').addEventListener('submit', async ev => {
    ev.preventDefault();
    const email = $('#email').value.trim(), password = $('#clave').value;
    const er = $('#login-error'), btn = $('#btn-login');
    er.hidden = true;
    if (!email || !password) { er.textContent = 'Escribe tu correo y contraseña.'; er.hidden = false; return; }
    btn.disabled = true; btn.textContent = 'Ingresando…';
    const espera = setTimeout(() => { $('#login-espera').hidden = false; }, 4000);
    try {
      const r = await api('/api/v1/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      S.token = r.access_token; S.rol = r.rol;
      try { localStorage.setItem('eh_token', S.token); localStorage.setItem('eh_rol', S.rol || ''); } catch (e) {}
      $('#clave').value = '';
      iniciarApp();
    } catch (e) {
      er.textContent = e.name === 'AbortError' ? 'El servidor no respondió. Intenta de nuevo.' : (e.message === 'Credenciales incorrectas' ? 'Correo o contraseña incorrectos.' : 'No se pudo ingresar: ' + e.message);
      er.hidden = false;
    } finally {
      clearTimeout(espera); $('#login-espera').hidden = true;
      btn.disabled = false; btn.textContent = 'Ingresar';
    }
  });
  $('#btn-salir').addEventListener('click', () => cerrarSesion());
  $('#btn-refrescar').addEventListener('click', () => render());

  /* ---------------- navegacion ---------------- */
  const TITULOS = { inicio: 'Inicio', dashboard: 'Dashboard', prediccion: 'Predicción' };
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => {
    S.tab = b.dataset.tab;
    document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('on', x === b));
    render();
  }));
  $('#zona').addEventListener('change', e => { S.zona = e.target.value; render(); });

  async function iniciarApp() {
    mostrar('app');
    try {
      const zs = await api('/api/v1/zonas/');
      S.zonas = Array.isArray(zs) ? zs : [];
    } catch (e) { S.zonas = []; }
    const sel = $('#zona');
    sel.innerHTML = '<option value="">Todas</option>' +
      S.zonas.map(z => '<option value="' + z.id_zona + '">' + G.esc(z.nombre_zona || ('Zona ' + z.id_zona)) + '</option>').join('');
    sel.value = S.zona;
    render();
  }

  function render() {
    $('#titulo-vista').textContent = TITULOS[S.tab];
    $('#zona-row').hidden = S.tab === 'prediccion';
    $('#aviso').hidden = true;
    const v = $('#vista');
    v.scrollTop = 0; window.scrollTo(0, 0);
    if (S.tab === 'inicio') return vistaInicio(v);
    if (S.tab === 'dashboard') return vistaDashboard(v);
    return vistaPrediccion(v);
  }
  const cargando = v => { v.innerHTML = '<div class="spinner" role="status" aria-label="Cargando"></div>'; };
  const fecha = iso => {
    const d = new Date(iso);
    return isNaN(d) ? '--' : d.toLocaleString('es-CO', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  };
  const seguro = p => p.catch(e => ({ __error: e.message }));
  const hayError = x => x && x.__error !== undefined;

  /* ================= INICIO (modulo informativo) ================= */
  async function vistaInicio(v) {
    cargando(v);
    const tk = ++renderTok;
    const [ult, p24, dist] = await Promise.all([
      seguro(est('ultimo-registro', zq())), seguro(est('promedio-24h', zq())), seguro(est('distribucion-estados', zq()))
    ]);
    if (tk !== renderTok || S.tab !== 'inicio') return;

    let tarjetaEstado;
    if (hayError(ult)) {
      tarjetaEstado = '<div class="card"><h2>Estado actual</h2><p class="err-card">No se pudo leer el último registro: ' + G.esc(ult.__error) + '</p></div>';
    } else {
      const t = ult.find(x => /temp/.test(x.tipo_medicion)), h = ult.find(x => /hum/.test(x.tipo_medicion));
      if (!t || !h) {
        tarjetaEstado = '<div class="card"><h2>Estado actual</h2><p>Aún no hay mediciones para esta zona.</p></div>';
      } else {
        const e = ESTADOS[clasificar(+t.valor, +h.valor)];
        const ultima = new Date(h.fecha_hora);
        const antiguo = !isNaN(ultima) && (Date.now() - ultima.getTime()) > 6 * 3600 * 1000;
        if (antiguo) { const a = $('#aviso'); a.textContent = 'El sensor no ha reportado recientemente. Se muestra el último dato guardado.'; a.hidden = false; }
        tarjetaEstado = '<div class="card"><h2>Estado actual</h2><p class="sub">Zona ' + G.esc(h.id_zona) + ' · último registro guardado</p>' +
          '<div class="estado-hero"><span class="badge" style="background:' + e.color + '">' + e.txt + '</span></div>' +
          '<div class="tiles"><div class="tile"><small>Humedad del suelo</small><b>' + G.fmt(h.valor) + '</b><i>%</i></div>' +
          '<div class="tile"><small>Temperatura del suelo</small><b>' + G.fmt(t.valor) + '</b><i>°C</i></div></div>' +
          '<p>' + e.consejo + '</p><p class="meta">Medido: ' + fecha(h.fecha_hora) + '</p></div>';
      }
    }

    let tarjeta24 = '';
    if (!hayError(p24) && p24.length) {
      const t = p24.find(x => /temp/.test(x.tipo_medicion)), h = p24.find(x => /hum/.test(x.tipo_medicion));
      tarjeta24 = '<div class="card"><h2>Resumen de 24 horas</h2><p class="sub">Promedios sobre el último día con datos</p><div class="tiles">' +
        '<div class="tile"><small>Humedad promedio</small><b>' + G.fmt(h && h.promedio) + '</b><i>%</i></div>' +
        '<div class="tile"><small>Temperatura promedio</small><b>' + G.fmt(t && t.promedio) + '</b><i>°C</i></div></div>' +
        '<p class="meta">' + G.fmt((h ? +h.registros : 0) + (t ? +t.registros : 0), 0) + ' mediciones analizadas</p></div>';
    }

    let tarjetaDist = '';
    if (!hayError(dist) && dist.length) {
      const total = dist.reduce((a, b) => a + (+b.muestras), 0);
      const orden = dist.slice().sort((a, b) => ORDEN.indexOf(a.estado) - ORDEN.indexOf(b.estado));
      tarjetaDist = '<div class="card"><h2>Historial por estado</h2><p class="sub">' + G.fmt(total, 0) + ' muestras clasificadas</p>' +
        orden.map(d => '<div class="prob"><span><span class="dot" style="background:' + ESTADOS[d.estado].color + '"></span>' + ESTADOS[d.estado].txt +
          '</span><span class="pista"><i style="width:' + (+d.porcentaje) + '%;background:' + ESTADOS[d.estado].color + '"></i></span><b>' + G.fmt(d.porcentaje) + '%</b></div>').join('') + '</div>';
    }

    v.innerHTML = tarjetaEstado + tarjeta24 + tarjetaDist +
      '<div class="card"><h2>¿Cómo funciona?</h2>' +
      '<p>Un sensor capacitivo y un termómetro DS18B20 miden la humedad y la temperatura del suelo en las zonas de reforestación. ' +
      'Un ESP32 envía cada lectura a la API, que la guarda en la base de datos. Esta app, el bot de Telegram y el propio ESP32 consultan esos datos siempre a través de la API.</p>' +
      '<div class="flow"><span>Sensores</span><em>→</em><span>ESP32</span><em>→</em><span>API</span><em>→</em><span>Base de datos</span><em>→</em><span>App / Bot</span></div></div>' +
      '<div class="card"><h2>Estados del suelo</h2><p class="sub">Los mismos umbrales que los LEDs del dispositivo</p><table>' +
      '<tr><th>Estado</th><th>Condición</th></tr>' +
      '<tr><td><span class="dot" style="background:#2e8b57"></span>Óptimo</td><td>Humedad ≥ 50 % y temp. ≤ 28 °C</td></tr>' +
      '<tr><td><span class="dot" style="background:#c98f00"></span>Precaución</td><td>Humedad &lt; 50 % o temp. &gt; 28 °C</td></tr>' +
      '<tr><td><span class="dot" style="background:#dd6a0b"></span>Estrés</td><td>Humedad &lt; 30 % o temp. &gt; 35 °C</td></tr>' +
      '<tr><td><span class="dot" style="background:#c62828"></span>Crítico</td><td>Humedad &lt; 15 % o temp. &gt; 40 °C</td></tr></table></div>';
  }
  let renderTok = 0;

  /* ================= DASHBOARD (5 graficos) ================= */
  function tarjetaGrafico(titulo, sub, cuerpo, ancho) {
    return '<section class="card' + (ancho ? ' ancho' : '') + '"><h2>' + G.esc(titulo) + '</h2><p class="sub">' + G.esc(sub) + '</p>' + cuerpo + '</section>';
  }
  const errGraf = x => '<p class="err-card">No se pudo cargar: ' + G.esc(x.__error) + '</p>';
  const corto = iso => { const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false }); };
  const diaCorto = iso => { const d = new Date(String(iso).slice(0, 10) + 'T12:00:00'); return isNaN(d) ? iso : d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' }); };

  async function vistaDashboard(v) {
    cargando(v);
    const tk = ++renderTok;
    const [hora, zonas, dist, ult, dias] = await Promise.all([
      seguro(est('promedio-por-hora', Object.assign({ tipo: 'humedad_suelo', horas: 24 }, zq()))),
      seguro(est('zonas-sobre-promedio', { tipo: 'humedad_suelo', solo_sobre_promedio: 'false' })),
      seguro(est('distribucion-estados', zq())),
      seguro(est('ultimo-registro', zq())),
      seguro(est('registros-por-dia', Object.assign({ dias: 10 }, zq())))
    ]);
    if (tk !== renderTok || S.tab !== 'dashboard') return;

    // 1. LINEA: humedad promedio por hora
    const g1 = hayError(hora) ? errGraf(hora) : G.linea({
      titulo: 'Humedad del suelo por hora', labels: hora.map(r => corto(r.hora)), values: hora.map(r => +r.promedio),
      tituloX: 'Hora del día', tituloY: 'Humedad (%)', unidad: '%', color: '#2f7fb8'
    });

    // 2. BARRAS: humedad promedio por zona
    let g2;
    if (hayError(zonas)) g2 = errGraf(zonas);
    else g2 = G.barras({
      titulo: 'Humedad promedio por zona', labels: zonas.map(z => z.nombre_zona || ('Zona ' + z.id_zona)), values: zonas.map(z => +z.promedio_zona),
      tituloX: 'Zona de reforestación', tituloY: 'Humedad (%)', color: '#1d6b46',
      referencia: zonas.length ? +zonas[0].promedio_general : null, refEtiqueta: 'General'
    });

    // 3. DONA: distribucion por estado
    const g3 = hayError(dist) ? errGraf(dist) : G.dona({
      titulo: 'Distribución por estado', centro: 'muestras',
      items: ORDEN.map(k => { const d = dist.find(x => x.estado === k); return { label: ESTADOS[k].txt, value: d ? +d.muestras : 0, color: ESTADOS[k].color }; })
    });

    // 4. MEDIDOR: humedad actual
    let g4;
    if (hayError(ult)) g4 = errGraf(ult);
    else {
      const h = ult.find(x => /hum/.test(x.tipo_medicion));
      g4 = G.medidor({
        titulo: 'Humedad actual', value: h ? +h.valor : null, min: 0, max: 100, unidad: '%',
        bandas: [
          { desde: 0, hasta: 15, color: ESTADOS.critico.color, etiqueta: '0–15 crítico' },
          { desde: 15, hasta: 30, color: ESTADOS.estres.color, etiqueta: '15–30 estrés' },
          { desde: 30, hasta: 50, color: ESTADOS.precaucion.color, etiqueta: '30–50 precaución' },
          { desde: 50, hasta: 100, color: ESTADOS.optimo.color, etiqueta: '50–100 óptimo' }
        ]
      });
    }

    // 5. COMBINADO: registros por dia (barras) + temperatura promedio (linea)
    let g5;
    if (hayError(dias)) g5 = errGraf(dias);
    else {
      const d = dias.slice().reverse().filter(r => r.temp_promedio !== null && r.temp_promedio !== undefined);
      g5 = d.length ? G.combinado({
        titulo: 'Registros y temperatura por día', labels: d.map(r => diaCorto(r.dia)),
        barras: d.map(r => +r.registros), linea: d.map(r => +r.temp_promedio),
        tituloX: 'Día', tituloBarras: 'Registros (n)', tituloLinea: 'Temperatura (°C)',
        etqBarras: 'Registros por día', etqLinea: 'Temp. promedio (°C)', colorBarras: '#9cc9b0', colorLinea: '#dd6a0b'
      }) : '<div class="chart-empty">Sin datos para mostrar</div>';
    }

    v.innerHTML = '<div class="dash">' +
      tarjetaGrafico('Humedad por hora', 'Línea · promedio por hora, últimas 24 h con datos (%)', g1, true) +
      tarjetaGrafico('Humedad actual', 'Medidor · último valor registrado (%)', g4) +
      tarjetaGrafico('Estados del suelo', 'Dona · porcentaje de muestras por estado', g3) +
      tarjetaGrafico('Humedad por zona', 'Barras · promedio histórico por zona (%)', g2) +
      tarjetaGrafico('Actividad y temperatura', 'Combinado · registros por día (barras) y °C promedio (línea)', g5, true) +
      '</div>';
  }

  /* ================= PREDICCION ================= */
  // Punto de enganche del modelo de Edge Impulse: si existe window.EI_MODEL.clasificar([temp, hum])
  // devuelve { etiqueta, probabilidades }, se usa ese; si no, reglas provisionales.
  async function predecir(t, h) {
    if (window.EI_MODEL && window.EI_MODEL.clasificar) {
      const r = await window.EI_MODEL.clasificar([t, h]);
      return { etiqueta: r.etiqueta, prob: r.probabilidades, motor: 'Modelo Edge Impulse' };
    }
    const et = clasificar(t, h);
    const prob = {}; ORDEN.forEach(k => prob[k] = k === et ? 1 : 0);
    return { etiqueta: et, prob, motor: 'Reglas provisionales (modelo de Edge Impulse pendiente)' };
  }

  function vistaPrediccion(v) {
    v.innerHTML = '<div class="card"><h2>Predecir el estado del suelo</h2><p class="sub">Ingresa los valores medidos y obtén la categoría</p>' +
      '<form id="form-pred" novalidate><div class="campos">' +
      '<div><label for="p-temp">Temperatura (°C)</label><input id="p-temp" type="number" inputmode="decimal" step="0.1" min="-10" max="80" placeholder="ej. 26.5" required></div>' +
      '<div><label for="p-hum">Humedad (%)</label><input id="p-hum" type="number" inputmode="decimal" step="1" min="0" max="100" placeholder="ej. 42" required></div>' +
      '</div><p id="p-error" class="error" role="alert" hidden></p><button class="btn" type="submit">Predecir</button></form>' +
      '<div id="p-res" aria-live="polite"></div></div>';
    $('#form-pred').addEventListener('submit', async ev => {
      ev.preventDefault();
      const er = $('#p-error'), res = $('#p-res');
      const t = parseFloat($('#p-temp').value), h = parseFloat($('#p-hum').value);
      er.hidden = true;
      if (isNaN(t) || isNaN(h)) { er.textContent = 'Completa los dos valores.'; er.hidden = false; res.innerHTML = ''; return; }
      if (h < 0 || h > 100) { er.textContent = 'La humedad debe estar entre 0 y 100 %.'; er.hidden = false; return; }
      if (t < -10 || t > 80) { er.textContent = 'La temperatura debe estar entre -10 y 80 °C.'; er.hidden = false; return; }
      const r = await predecir(t, h);
      const e = ESTADOS[r.etiqueta];
      res.innerHTML = '<div class="resultado" style="background:' + e.color + '"><small>Categoría predicha</small><h3>' + e.txt + '</h3><p>' + e.consejo + '</p></div>' +
        '<div class="barras-prob">' + ORDEN.map(k => '<div class="prob"><span>' + ESTADOS[k].txt + '</span><span class="pista"><i style="width:' +
          Math.round((r.prob[k] || 0) * 100) + '%;background:' + ESTADOS[k].color + '"></i></span><b>' + Math.round((r.prob[k] || 0) * 100) + '%</b></div>').join('') + '</div>' +
        '<p class="nota">Motor: ' + G.esc(r.motor) + '</p>';
    });
  }

  /* ---------------- arranque ---------------- */
  if ('serviceWorker' in navigator) { navigator.serviceWorker.register('sw.js').catch(() => {}); }
  if (S.token) iniciarApp(); else mostrar('login');
})();
