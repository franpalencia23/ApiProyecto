/* charts.js - graficos SVG propios (sin librerias externas).
   Cinco tipos: linea, barras, dona (pastel), medidor (gauge) y combinado barras+linea.
   Todos devuelven un string HTML con titulo de ejes, unidades y etiquetas. */
(function (global) {
  'use strict';

  const W = 360, H = 230;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
  function fmt(v, d) {
    if (v === null || v === undefined || isNaN(v)) return '--';
    return Number(v).toLocaleString('es-CO', { maximumFractionDigits: d === undefined ? 1 : d });
  }
  function vacio(msg) {
    return '<div class="chart-empty">' + esc(msg || 'Sin datos para mostrar') + '</div>';
  }

  // Escala "bonita" para el eje Y
  function escala(min, max, n) {
    n = n || 5;
    if (!isFinite(min) || !isFinite(max)) { min = 0; max = 1; }
    if (min === max) { max = min + 1; }
    const paso0 = (max - min) / (n - 1);
    const mag = Math.pow(10, Math.floor(Math.log10(paso0)));
    const norm = paso0 / mag;
    const paso = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * mag;
    const lo = Math.floor(min / paso) * paso;
    const hi = Math.ceil(max / paso) * paso;
    const ticks = [];
    for (let v = lo; v <= hi + paso / 2; v += paso) ticks.push(+v.toFixed(10));
    return { lo, hi, ticks };
  }

  // Marco comun: ejes, rejilla y titulos de ejes
  function marco(o) {
    const m = { l: 46, r: o.derecha ? 46 : 14, t: 16, b: 50 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const yScale = o.escalaY;
    const y = v => m.t + ih - ((v - yScale.lo) / (yScale.hi - yScale.lo)) * ih;
    let s = '';
    yScale.ticks.forEach(t => {
      s += '<line class="grid" x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(t) + '" y2="' + y(t) + '"/>';
      s += '<text class="ax" x="' + (m.l - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end">' + fmt(t, 1) + '</text>';
    });
    s += '<line class="axis" x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + (m.t + ih) + '" y2="' + (m.t + ih) + '"/>';
    // titulo eje Y (rotado)
    s += '<text class="axt" transform="translate(12 ' + (m.t + ih / 2) + ') rotate(-90)" text-anchor="middle">' + esc(o.tituloY) + '</text>';
    // titulo eje X
    s += '<text class="axt" x="' + (m.l + iw / 2) + '" y="' + (H - 6) + '" text-anchor="middle">' + esc(o.tituloX) + '</text>';
    if (o.derecha) {
      const e2 = o.derecha.escala;
      const y2 = v => m.t + ih - ((v - e2.lo) / (e2.hi - e2.lo)) * ih;
      e2.ticks.forEach(t => {
        s += '<text class="ax" x="' + (W - m.r + 6) + '" y="' + (y2(t) + 4) + '">' + fmt(t, 1) + '</text>';
      });
      s += '<text class="axt" transform="translate(' + (W - 8) + ' ' + (m.t + ih / 2) + ') rotate(90)" text-anchor="middle">' + esc(o.derecha.titulo) + '</text>';
    }
    return { svg: s, m, iw, ih, y };
  }

  // Etiquetas del eje X (se adelgazan para que no se encimen)
  function etiquetasX(labels, xPos, m, ih) {
    const maxEtq = 6;
    const k = Math.max(1, Math.ceil(labels.length / maxEtq));
    let s = '';
    labels.forEach((l, i) => {
      if (i % k !== 0 && i !== labels.length - 1) return;
      if (i !== labels.length - 1 && labels.length - 1 - i < k / 2 && k > 1) return;
      s += '<text class="ax" x="' + xPos(i) + '" y="' + (m.t + ih + 16) + '" text-anchor="middle">' + esc(l) + '</text>';
    });
    return s;
  }

  function envolver(aria, contenido) {
    return '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(aria) + '" class="chart-svg">' + contenido + '</svg>';
  }

  /* ---------- 1. LINEA ---------- */
  function linea(o) {
    if (!o.values || !o.values.length) return vacio();
    const e = escala(Math.min.apply(null, o.values) - 0.0, Math.max.apply(null, o.values), 5);
    const f = marco({ escalaY: e, tituloY: o.tituloY, tituloX: o.tituloX });
    const n = o.values.length;
    const x = i => f.m.l + (n === 1 ? f.iw / 2 : (i / (n - 1)) * f.iw);
    const pts = o.values.map((v, i) => x(i) + ',' + f.y(v));
    let s = f.svg + etiquetasX(o.labels, x, f.m, f.ih);
    if (n > 1) {
      s += '<polygon class="area" style="fill:' + o.color + '" points="' + x(0) + ',' + (f.m.t + f.ih) + ' ' + pts.join(' ') + ' ' + x(n - 1) + ',' + (f.m.t + f.ih) + '"/>';
      s += '<polyline class="ln" style="stroke:' + o.color + '" points="' + pts.join(' ') + '"/>';
    }
    if (n <= 40) o.values.forEach((v, i) => { s += '<circle r="3" cx="' + x(i) + '" cy="' + f.y(v) + '" style="fill:' + o.color + '"/>'; });
    const ult = o.values[n - 1];
    s += '<text class="val" x="' + x(n - 1) + '" y="' + (f.y(ult) - 8) + '" text-anchor="' + (n > 1 ? 'end' : 'middle') + '">' + fmt(ult) + ' ' + esc(o.unidad || '') + '</text>';
    return envolver(o.titulo + '. Ultimo valor ' + fmt(ult) + ' ' + (o.unidad || ''), s);
  }

  /* ---------- 2. BARRAS ---------- */
  function barras(o) {
    if (!o.values || !o.values.length) return vacio();
    const e = escala(0, Math.max.apply(null, o.values), 5);
    const f = marco({ escalaY: e, tituloY: o.tituloY, tituloX: o.tituloX });
    const n = o.values.length, paso = f.iw / n, bw = Math.min(46, paso * 0.62);
    let s = f.svg;
    o.values.forEach((v, i) => {
      const cx = f.m.l + paso * (i + 0.5);
      const top = f.y(v);
      s += '<rect rx="3" x="' + (cx - bw / 2) + '" y="' + top + '" width="' + bw + '" height="' + Math.max(0, f.m.t + f.ih - top) + '" style="fill:' + (o.colores ? o.colores[i % o.colores.length] : o.color) + '"/>';
      s += '<text class="val" x="' + cx + '" y="' + (top - 5) + '" text-anchor="middle">' + fmt(v) + '</text>';
      const l = String(o.labels[i]);
      s += '<text class="ax" x="' + cx + '" y="' + (f.m.t + f.ih + 16) + '" text-anchor="middle">' + esc(l.length > 9 ? l.slice(0, 8) + '…' : l) + '</text>';
    });
    if (o.referencia !== undefined && o.referencia !== null && !isNaN(o.referencia)) {
      s += '<line class="ref" x1="' + f.m.l + '" x2="' + (W - f.m.r) + '" y1="' + f.y(o.referencia) + '" y2="' + f.y(o.referencia) + '"/>';
      s += '<text class="ref-t" x="' + (W - f.m.r) + '" y="' + (f.y(o.referencia) - 4) + '" text-anchor="end">' + esc(o.refEtiqueta || 'Promedio') + ' ' + fmt(o.referencia) + '</text>';
    }
    return envolver(o.titulo, s);
  }

  /* ---------- 3. DONA / PASTEL ---------- */
  function polar(cx, cy, r, ang) { return [cx + r * Math.cos(ang), cy + r * Math.sin(ang)]; }
  function arco(cx, cy, r0, r1, a0, a1) {
    const g = a1 - a0 > Math.PI ? 1 : 0;
    const p0 = polar(cx, cy, r1, a0), p1 = polar(cx, cy, r1, a1), p2 = polar(cx, cy, r0, a1), p3 = polar(cx, cy, r0, a0);
    return 'M' + p0 + ' A' + r1 + ',' + r1 + ' 0 ' + g + ' 1 ' + p1 + ' L' + p2 + ' A' + r0 + ',' + r0 + ' 0 ' + g + ' 0 ' + p3 + ' Z';
  }
  function dona(o) {
    const total = (o.items || []).reduce((a, b) => a + b.value, 0);
    if (!total) return vacio();
    const cx = 110, cy = 105, r1 = 86, r0 = 50;
    let a = -Math.PI / 2, s = '';
    o.items.forEach(it => {
      if (it.value <= 0) return;
      const frac = it.value / total;
      const a1 = a + (frac >= 0.9999 ? 2 * Math.PI - 0.0001 : frac * 2 * Math.PI);
      s += '<path d="' + arco(cx, cy, r0, r1, a, a1) + '" style="fill:' + it.color + '"><title>' + esc(it.label) + ': ' + fmt(frac * 100) + '%</title></path>';
      a = a1;
    });
    s += '<text class="big" x="' + cx + '" y="' + (cy + 4) + '" text-anchor="middle">' + fmt(total, 0) + '</text>';
    s += '<text class="ax" x="' + cx + '" y="' + (cy + 22) + '" text-anchor="middle">' + esc(o.centro || 'muestras') + '</text>';
    const svg = '<svg viewBox="0 0 220 210" role="img" aria-label="' + esc(o.titulo) + '" class="chart-svg donut">' + s + '</svg>';
    const leyenda = '<ul class="legend">' + o.items.map(it =>
      '<li><span class="sw" style="background:' + it.color + '"></span><span class="lg-n">' + esc(it.label) + '</span><b>' +
      fmt(it.value / total * 100) + '%</b><small>' + fmt(it.value, 0) + '</small></li>').join('') + '</ul>';
    return '<div class="donut-wrap">' + svg + leyenda + '</div>';
  }

  /* ---------- 4. MEDIDOR (GAUGE) ---------- */
  function medidor(o) {
    const cx = 150, cy = 150, r1 = 118, r0 = 90;
    const ang = v => Math.PI + (Math.min(Math.max(v, o.min), o.max) - o.min) / (o.max - o.min) * Math.PI;
    let s = '';
    o.bandas.forEach(b => {
      s += '<path d="' + arco(cx, cy, r0, r1, ang(b.desde), ang(b.hasta)) + '" style="fill:' + b.color + '"/>';
    });
    // marcas
    [o.min, (o.min + o.max) / 2, o.max].forEach(v => {
      const p = polar(cx, cy, r1 + 12, ang(v));
      s += '<text class="ax" x="' + p[0] + '" y="' + (p[1] + 4) + '" text-anchor="middle">' + fmt(v, 0) + '</text>';
    });
    if (o.value !== null && o.value !== undefined && !isNaN(o.value)) {
      const a = ang(o.value), p = polar(cx, cy, r1 - 4, a), b1 = polar(cx, cy, 8, a + Math.PI / 2), b2 = polar(cx, cy, 8, a - Math.PI / 2);
      s += '<polygon class="needle" points="' + p + ' ' + b1 + ' ' + b2 + '"/><circle class="needle" cx="' + cx + '" cy="' + cy + '" r="9"/>';
      s += '<text class="big" x="' + cx + '" y="' + (cy + 38) + '" text-anchor="middle">' + fmt(o.value) + ' ' + esc(o.unidad) + '</text>';
    } else {
      s += '<text class="ax" x="' + cx + '" y="' + (cy + 38) + '" text-anchor="middle">Sin lectura</text>';
    }
    const leyenda = '<ul class="legend row">' + o.bandas.map(b =>
      '<li><span class="sw" style="background:' + b.color + '"></span>' + esc(b.etiqueta) + '</li>').join('') + '</ul>';
    return '<svg viewBox="0 0 300 200" role="img" aria-label="' + esc(o.titulo + ': ' + fmt(o.value) + ' ' + o.unidad) + '" class="chart-svg gauge">' + s + '</svg>' + leyenda;
  }

  /* ---------- 5. COMBINADO: barras + linea con dos ejes ---------- */
  function combinado(o) {
    if (!o.labels || !o.labels.length) return vacio();
    const e1 = escala(0, Math.max.apply(null, o.barras), 5);
    const lmin = Math.min.apply(null, o.linea), lmax = Math.max.apply(null, o.linea);
    const e2 = escala(Math.floor(lmin - 1), Math.ceil(lmax + 1), 5);
    const f = marco({ escalaY: e1, tituloY: o.tituloBarras, tituloX: o.tituloX, derecha: { escala: e2, titulo: o.tituloLinea } });
    const n = o.labels.length, paso = f.iw / n, bw = Math.min(30, paso * 0.6);
    const x = i => f.m.l + paso * (i + 0.5);
    const y2 = v => f.m.t + f.ih - ((v - e2.lo) / (e2.hi - e2.lo)) * f.ih;
    let s = f.svg;
    o.barras.forEach((v, i) => {
      const top = f.y(v);
      s += '<rect rx="2" x="' + (x(i) - bw / 2) + '" y="' + top + '" width="' + bw + '" height="' + Math.max(0, f.m.t + f.ih - top) + '" style="fill:' + o.colorBarras + '"/>';
    });
    s += etiquetasX(o.labels, x, f.m, f.ih);
    s += '<polyline class="ln" style="stroke:' + o.colorLinea + '" points="' + o.linea.map((v, i) => x(i) + ',' + y2(v)).join(' ') + '"/>';
    o.linea.forEach((v, i) => { s += '<circle r="3" cx="' + x(i) + '" cy="' + y2(v) + '" style="fill:' + o.colorLinea + '"/>'; });
    const leyenda = '<ul class="legend row"><li><span class="sw" style="background:' + o.colorBarras + '"></span>' + esc(o.etqBarras) +
      '</li><li><span class="sw line" style="background:' + o.colorLinea + '"></span>' + esc(o.etqLinea) + '</li></ul>';
    return envolver(o.titulo, s) + leyenda;
  }

  global.Graficos = { linea, barras, dona, medidor, combinado, fmt, esc };
})(window);
