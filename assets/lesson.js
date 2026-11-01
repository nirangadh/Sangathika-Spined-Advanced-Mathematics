// සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna. MIT licence, see LICENSE.
// Shared behaviour for every lesson page. All teaching text is already in the HTML:
// this script only reveals, hides, checks and remembers. Progress is kept in this
// browser only, under one key per leaf, and is never sent anywhere.
(function(){
'use strict';

/* ---------- storage, guarded: private windows and blocked storage simply forget ---------- */
var leaf = document.documentElement.getAttribute('data-leaf') || 'site';
var KEY = 'sam-progress-' + leaf;
function load(){ try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
function save(s){ try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} }

/* ---------- theme toggle ---------- */
var tb = document.getElementById('themeBtn'), root = document.documentElement;
function cur(){ var t = root.getAttribute('data-theme'); if (t) return t; return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }
function paint(){ if (!tb) return; var d = cur() === 'dark'; tb.textContent = d ? 'Light' : 'Dark'; tb.setAttribute('aria-pressed', d ? 'true' : 'false'); }
if (tb){ tb.addEventListener('click', function(){ var n = cur() === 'dark' ? 'light' : 'dark'; root.setAttribute('data-theme', n); try { localStorage.setItem('sam-theme', n); } catch (e) {} paint(); }); paint(); }

/* ---------- choice questions ----------
   <div class="q"> ... <div class="opts"><button class="opt" data-correct> ... </div><p class="fb" hidden>explanation</p></div>
   Groups (warm-up, sorting plate, quiz) are any element with data-group; its score line is [data-score] inside it. */
function verdict(ok, group){
  var labels = (group && group.getAttribute('data-labels') || 'Right.|Not quite.').split('|');
  return '<b class="' + (ok ? 'r' : 'w') + '">' + (ok ? labels[0] : labels[1]) + '</b> ';
}
document.querySelectorAll('[data-group]').forEach(function(group){
  var qs = group.querySelectorAll('.q'), first = [];
  var scoreEl = group.querySelector('[data-score]');
  function score(){
    if (!scoreEl) return;
    var answered = first.filter(function(x){ return x !== undefined; }).length;
    var right = first.filter(function(x){ return x === true; }).length;
    scoreEl.textContent = answered ? (answered + ' of ' + qs.length + ' answered, ' + right + ' right on the first try.') : scoreEl.getAttribute('data-empty') || '';
  }
  qs.forEach(function(q, i){
    var fb = q.querySelector('.fb'), body = fb ? fb.innerHTML : '';
    q.querySelectorAll('.opt').forEach(function(b){
      b.type = 'button';
      b.addEventListener('click', function(){
        var ok = b.hasAttribute('data-correct');
        if (first[i] === undefined) first[i] = ok;
        q.querySelectorAll('.opt').forEach(function(x){ x.classList.remove('right', 'wrong'); });
        b.classList.add(ok ? 'right' : 'wrong');
        if (!ok && group.hasAttribute('data-show-right')){ var r = q.querySelector('.opt[data-correct]'); if (r) r.classList.add('right'); }
        if (fb){ fb.innerHTML = verdict(ok, group) + body; fb.hidden = false; }
        score();
      });
    });
  });
  var reset = group.querySelector('[data-reset]');
  if (reset) reset.addEventListener('click', function(){
    first = [];
    qs.forEach(function(q){ q.querySelectorAll('.opt').forEach(function(x){ x.classList.remove('right', 'wrong'); }); var fb = q.querySelector('.fb'); if (fb) fb.hidden = true; });
    score();
  });
  score();
});

/* ---------- reveal toggles: a button with data-reveal="selector" swaps .hid and .ans inside the target ---------- */
document.querySelectorAll('[data-reveal]').forEach(function(btn){
  var on = btn.getAttribute('data-on') || 'Hide', off = btn.textContent;
  btn.addEventListener('click', function(){
    var show = btn.getAttribute('aria-pressed') !== 'true';
    btn.setAttribute('aria-pressed', String(show)); btn.textContent = show ? on : off;
    document.querySelectorAll(btn.getAttribute('data-reveal')).forEach(function(el){
      var h = el.querySelector('.hid'), a = el.querySelector('.ans');
      if (h) h.hidden = show; if (a) a.hidden = !show;
    });
  });
});

/* ---------- challenges ----------
   <article class="challenge" id="challenge-N-K" data-level="seed|branch|canopy" data-answer="12" data-mode="number|set|text">
   A form.commit, three details.hint, a details.solution[hidden] and p.result[hidden].
   Hints open in order; the solution appears only after an answer is committed. */
var state = load();
document.querySelectorAll('.challenge').forEach(function(ch){
  var id = ch.id, st = state[id] || (state[id] = { hints: 0, committed: false, solved: false });
  var hints = Array.prototype.slice.call(ch.querySelectorAll('details.hint'));
  var count = ch.querySelector('.hint-count'), sol = ch.querySelector('details.solution');
  var form = ch.querySelector('form.commit'), res = ch.querySelector('.result');
  var input = form && form.querySelector('input, textarea');
  function paintHints(){
    hints.forEach(function(h, i){ h.hidden = i > st.hints; if (i < st.hints) h.open = h.open || false; });
    if (count) count.textContent = 'Hints used: ' + st.hints + ' of ' + hints.length;
  }
  hints.forEach(function(h, i){
    h.addEventListener('toggle', function(){
      if (h.open && i + 1 > st.hints){ st.hints = i + 1; save(state); paintHints(); }
    });
  });
  function nums(s){ return (String(s).replace(/−/g, '-').match(/-?\d+(\.\d+)?/g) || []).map(Number); }
  function check(v){
    var mode = ch.getAttribute('data-mode') || 'text', ans = ch.getAttribute('data-answer');
    if (mode === 'text' || ans === null) return null;
    var got = nums(v), want = nums(ans), tol = parseFloat(ch.getAttribute('data-tolerance') || '0.01');
    if (mode === 'number') return got.length > 0 && Math.abs(got[0] - want[0]) <= tol;
    if (mode === 'set'){
      if (got.length !== want.length) return false;
      got.sort(function(a, b){ return a - b; }); want.sort(function(a, b){ return a - b; });
      return got.every(function(g, i){ return Math.abs(g - want[i]) <= tol; });
    }
    return null;
  }
  function showResult(ok){
    if (!res) return;
    res.hidden = false;
    if (ok === true){ res.className = 'result ok'; res.textContent = 'That matches. Read the solution to check your route as well as your answer.'; }
    else if (ok === false){ res.className = 'result no'; res.textContent = 'That does not match. You can try again, open a hint, or read the solution and find where the routes part.'; }
    else { res.className = 'result done'; res.textContent = 'Committed. Now compare your reasoning with the solution.'; }
  }
  if (form) form.addEventListener('submit', function(e){
    e.preventDefault();
    var v = input ? input.value.trim() : '';
    if (!v){ if (input) input.focus(); return; }
    var ok = check(v);
    st.committed = true; if (ok === true) st.solved = true; save(state);
    showResult(ok);
    if (sol) sol.hidden = false;
  });
  if (sol) sol.hidden = !st.committed;   /* a commit made on an earlier visit keeps the solution open */
  paintHints();
});
save(state);
})();
