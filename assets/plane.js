// සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna. MIT licence, see LICENSE.
// Shared drawing helper for lesson plates: a coordinate plane on a canvas, arrows, dots,
// labels, dragging and redraw plumbing. New lessons load it with
//   <script src="../../assets/plane.js" defer></script>
// and use the PL namespace. It holds no mathematics: the maths lives in each leaf's sam.js.
(function(){
'use strict';
var root = document.documentElement;
var C = {};
var KEYS = ['ink', 'muted', 'rule', 'grid', 'surface', 'paper', 'v', 'av', 'eig', 'res', 'res-soft', 'eig-soft', 'fill', 'tgrid', 'crimson', 'steel'];
function readColors(){
  var s = getComputedStyle(root);
  KEYS.forEach(function(k){ C[k] = s.getPropertyValue('--' + k).trim() || '#888'; });
}
readColors();
var MONO = '"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace';
var SERIF = '"STIX Two Text", "Cambria Math", Cambria, Georgia, serif';
var VFONT = 'italic 600 17px ' + SERIF;
var MINUS = '−';
var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* numbers written for people: true minus sign, no trailing zeros */
function fmt(n, d){
  if (d === undefined) d = 2;
  if (Math.abs(n) < 0.5 * Math.pow(10, -d)) n = 0;
  var s = n.toFixed(d);
  if (s.indexOf('.') >= 0) s = s.replace(/0+$/, '').replace(/\.$/, '');
  if (s === '-0') s = '0';
  return s.replace('-', MINUS);
}
function pair(x, y, d){ return '(' + fmt(x, d) + ', ' + fmt(y, d) + ')'; }
function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }

/* a plane over the rectangle r = {x0, x1, y0, y1} on canvas cv */
function Plane(cv, r){ this.cv = cv; this.r = r; this.ctx = cv.getContext('2d'); this.W = 1; this.H = 1; }
Plane.prototype.fit = function(){
  var b = this.cv.getBoundingClientRect(), d = window.devicePixelRatio || 1;
  this.W = Math.max(1, b.width); this.H = Math.max(1, b.height);
  var w = Math.round(this.W * d), h = Math.round(this.H * d);
  if (this.cv.width !== w) this.cv.width = w;
  if (this.cv.height !== h) this.cv.height = h;
  this.ctx.setTransform(d, 0, 0, d, 0, 0);
  this.ctx.clearRect(0, 0, this.W, this.H);
};
Plane.prototype.X = function(x){ return (x - this.r.x0) / (this.r.x1 - this.r.x0) * this.W; };
Plane.prototype.Y = function(y){ return this.H - (y - this.r.y0) / (this.r.y1 - this.r.y0) * this.H; };
Plane.prototype.inv = function(px, py){
  return { x: this.r.x0 + px / this.W * (this.r.x1 - this.r.x0), y: this.r.y0 + (this.H - py) / this.H * (this.r.y1 - this.r.y0) };
};
Plane.prototype.unit = function(){ return this.W / (this.r.x1 - this.r.x0); };
Plane.prototype.grid = function(o){
  o = o || {};
  var c = this.ctx, r = this.r, x, y, every = o.every || 2;
  c.save();
  c.lineWidth = 1; c.strokeStyle = C.grid; c.beginPath();
  for (x = Math.ceil(r.x0); x <= r.x1; x++){ var px = Math.round(this.X(x)) + 0.5; c.moveTo(px, 0); c.lineTo(px, this.H); }
  for (y = Math.ceil(r.y0); y <= r.y1; y++){ var py = Math.round(this.Y(y)) + 0.5; c.moveTo(0, py); c.lineTo(this.W, py); }
  c.stroke();
  c.strokeStyle = C.muted; c.globalAlpha = 0.6; c.lineWidth = 1.25; c.beginPath();
  c.moveTo(0, this.Y(0)); c.lineTo(this.W, this.Y(0));
  c.moveTo(this.X(0), 0); c.lineTo(this.X(0), this.H);
  c.stroke(); c.globalAlpha = 1;
  c.fillStyle = C.muted; c.font = '10.5px ' + MONO;
  c.textAlign = 'center'; c.textBaseline = 'top';
  for (x = Math.ceil(r.x0 / every) * every; x < r.x1; x += every){ if (x === 0 || x <= r.x0) continue; c.fillText(fmt(x), this.X(x), this.Y(0) + 4); }
  c.textAlign = 'right'; c.textBaseline = 'middle';
  for (y = Math.ceil(r.y0 / every) * every; y < r.y1; y += every){ if (y === 0 || y <= r.y0) continue; c.fillText(fmt(y), this.X(0) - 5, this.Y(y)); }
  if (o.names){
    c.font = '11px ' + MONO;
    c.textAlign = 'right'; c.textBaseline = 'bottom'; c.fillText(o.names[0], this.W - 6, this.Y(0) - 4);
    c.textAlign = 'left'; c.textBaseline = 'top'; c.fillText(o.names[1], this.X(0) + 6, 6);
  }
  c.restore();
};
Plane.prototype.line = function(x0, y0, x1, y1, col, o){
  o = o || {}; var c = this.ctx; c.save();
  c.globalAlpha = o.alpha == null ? 1 : o.alpha; c.strokeStyle = col; c.lineWidth = o.w || 1.5;
  if (o.dash) c.setLineDash(o.dash);
  c.beginPath(); c.moveTo(this.X(x0), this.Y(y0)); c.lineTo(this.X(x1), this.Y(y1)); c.stroke(); c.restore();
};
/* the whole line through (ox, oy) in direction (dx, dy), clipped by the canvas */
Plane.prototype.fullLine = function(dx, dy, col, o){
  o = o || {}; var k = 1000, ox = o.ox || 0, oy = o.oy || 0;
  this.line(ox - k * dx, oy - k * dy, ox + k * dx, oy + k * dy, col, o);
};
Plane.prototype.arrow = function(x0, y0, x1, y1, col, o){
  o = o || {};
  var c = this.ctx, a = this.X(x0), b = this.Y(y0), e = this.X(x1), f = this.Y(y1);
  var dx = e - a, dy = f - b, L = Math.hypot(dx, dy), w = o.w || 2.75;
  c.save(); c.globalAlpha = o.alpha == null ? 1 : o.alpha; c.strokeStyle = col; c.fillStyle = col; c.lineWidth = w; c.lineCap = 'round';
  if (L < 2){ c.beginPath(); c.arc(a, b, w * 1.4, 0, Math.PI * 2); c.fill(); c.restore(); return; }
  var h = Math.min(o.head || (8 + w * 2), L * 0.45), ux = dx / L, uy = dy / L, bx = e - ux * h, by = f - uy * h, hw = h * 0.5;
  if (o.dash) c.setLineDash(o.dash);
  c.beginPath(); c.moveTo(a, b); c.lineTo(bx + ux, by + uy); c.stroke(); c.setLineDash([]);
  c.beginPath(); c.moveTo(e, f); c.lineTo(bx - uy * hw, by + ux * hw); c.lineTo(bx + uy * hw, by - ux * hw); c.closePath(); c.fill();
  c.restore();
};
Plane.prototype.dot = function(x, y, rad, col, o){
  o = o || {}; var c = this.ctx, px = this.X(x), py = this.Y(y); c.save();
  if (o.square){ c.fillStyle = col; c.fillRect(px - rad, py - rad, rad * 2, rad * 2); c.strokeStyle = C.surface; c.lineWidth = 1.5; c.strokeRect(px - rad, py - rad, rad * 2, rad * 2); }
  else if (o.ring){ c.fillStyle = o.fill || C.surface; c.strokeStyle = col; c.lineWidth = o.lw || 2.5; c.beginPath(); c.arc(px, py, rad, 0, Math.PI * 2); c.fill(); c.stroke(); }
  else { c.fillStyle = col; c.beginPath(); c.arc(px, py, rad, 0, Math.PI * 2); c.fill(); }
  c.restore();
};
Plane.prototype.text = function(s, x, y, col, o){
  o = o || {}; var c = this.ctx; c.save();
  c.font = o.font || ('500 12.5px ' + MONO); c.textAlign = o.align || 'center'; c.textBaseline = o.base || 'middle';
  var px = this.X(x) + (o.dx || 0), py = this.Y(y) + (o.dy || 0);
  c.lineJoin = 'round'; c.lineWidth = 4; c.strokeStyle = C.surface; c.strokeText(s, px, py);
  c.fillStyle = col; c.fillText(s, px, py); c.restore();
};
/* a label beside the middle of segment P to Q, pushed off it on the side chosen by sign */
function sideLabel(p, s, P, Q, col, sign, off){
  var dx = Q[0] - P[0], dy = Q[1] - P[1], L = Math.hypot(dx, dy) || 1;
  var nx = -dy / L * sign, ny = dx / L * sign, mx = (P[0] + Q[0]) / 2, my = (P[1] + Q[1]) / 2;
  p.text(s, mx + nx * (off || 0.55), my + ny * (off || 0.55), col, { font: VFONT });
}

/* dragging: handles() returns [{id, x, y}], onDrag(id, x, y) receives plane coordinates */
function draggable(plane, handles, onDrag){
  var cv = plane.cv, active = null;
  function pt(e){ var r = cv.getBoundingClientRect(); return { px: e.clientX - r.left, py: e.clientY - r.top }; }
  cv.addEventListener('pointerdown', function(e){
    var q = pt(e), best = null, bd = 30;
    handles().forEach(function(h){ var d = Math.hypot(plane.X(h.x) - q.px, plane.Y(h.y) - q.py); if (d < bd){ bd = d; best = h.id; } });
    if (best === null) return;
    active = best; try { cv.setPointerCapture(e.pointerId); } catch (err) {}
    e.preventDefault(); move(e);
  });
  function move(e){
    if (active === null) return;
    var q = pt(e), p = plane.inv(q.px, q.py);
    requestAnimationFrame(function(){ onDrag(active, p.x, p.y); });
  }
  cv.addEventListener('pointermove', move);
  cv.addEventListener('pointerup', function(){ active = null; });
  cv.addEventListener('pointercancel', function(){ active = null; });
}

/* redraw on resize, theme change and font load */
var redraws = [];
function watch(cv, fn){
  redraws.push(fn);
  if (window.ResizeObserver) new ResizeObserver(function(){ fn(); }).observe(cv);
}
function redrawAll(){ readColors(); redraws.forEach(function(f){ f(); }); }
try { window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', redrawAll); } catch (e) {}
new MutationObserver(redrawAll).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
if (document.fonts && document.fonts.ready) document.fonts.ready.then(redrawAll);

window.PL = { C: C, MONO: MONO, SERIF: SERIF, VFONT: VFONT, reduceMotion: reduceMotion,
  fmt: fmt, pair: pair, clamp: clamp, Plane: Plane, sideLabel: sideLabel, draggable: draggable, watch: watch, redrawAll: redrawAll };
})();
