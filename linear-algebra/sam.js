// සංගතික · Sangathika · SAM. © 2026 Niranga Dharmaratna. MIT licence, see LICENSE.
// The Linear Algebra library. Each function is added by the lesson that introduces it,
// and later lessons call it rather than redefining it. Read top to bottom, it is the
// leaf's grammar: one rule at a time, in the order you meet them.
// A vector is a pair [x, y]. A 2 x 2 matrix is a list of four numbers read row by row:
// [a, b, c, d] means the rows (a, b) and (c, d).

// page 01: vec. A vector is a size and a direction, written as its two components.
function vec(x, y){ return [x, y]; }

// page 01: add. One move, then the other: add the easts, add the norths.
function add(u, v){ return [u[0] + v[0], u[1] + v[1]]; }

// page 01: sub. u minus v is the move from the tip of v to the tip of u.
function sub(u, v){ return [u[0] - v[0], u[1] - v[1]]; }

// page 01: scale. Multiply each component by k: same line, new length.
function scale(k, v){ return [k * v[0], k * v[1]]; }

// page 01: len. Pythagoras turns components into a length.
function len(v){ return Math.hypot(v[0], v[1]); }

// page 01: bearing. Degrees clockwise from north, the way a ship's officer reads direction.
function bearing(v){ return ((90 - Math.atan2(v[1], v[0]) * 180 / Math.PI) % 360 + 360) % 360; }

// page 06: apply. A matrix moves a vector: x copies of the first column plus y copies of the second.
// (Used early by page 17, which comes before page 06 is written; page 06 introduces it properly.)
function apply(A, v){ return [A[0] * v[0] + A[1] * v[1], A[2] * v[0] + A[3] * v[1]]; }

// page 09: det. How much the matrix scales area: (top-left)(bottom-right) minus (top-right)(bottom-left).
// (Used early by page 17; page 09 introduces it properly.)
function det(A){ return A[0] * A[3] - A[1] * A[2]; }

// page 17: eigen. The directions a matrix only stretches, from det(A - λI) = 0.
// Returns the trace, determinant, discriminant, a kind ('two', 'one', 'scalar', 'complex')
// and the eigenvalue and unit direction of each eigenvector it finds.
function eigen(A){
  var a = A[0], b = A[1], c = A[2], d = A[3], eps = 1e-9;
  var tr = a + d, dt = det(A), disc = tr * tr - 4 * dt;
  function unit(v){ var L = len(v); return [v[0] / L, v[1] / L]; }
  var out = { tr: tr, det: dt, disc: disc };
  if (Math.abs(b) <= eps && Math.abs(c) <= eps){
    if (Math.abs(a - d) <= eps){ out.kind = 'scalar'; out.pairs = [{ l: a, v: null }]; return out; }
    out.kind = 'two'; out.pairs = [{ l: a, v: [1, 0] }, { l: d, v: [0, 1] }].sort(function(p, q){ return q.l - p.l; }); return out;
  }
  if (disc < -eps){ out.kind = 'complex'; out.re = tr / 2; out.im = Math.sqrt(-disc) / 2; out.pairs = []; return out; }
  var s = Math.sqrt(Math.max(disc, 0));
  function dir(l){ return Math.abs(b) > eps ? [b, l - a] : [l - d, c]; }
  if (s <= eps){ out.kind = 'one'; out.pairs = [{ l: tr / 2, v: unit(dir(tr / 2)) }]; return out; }
  var l1 = (tr + s) / 2, l2 = (tr - s) / 2;
  out.kind = 'two'; out.pairs = [{ l: l1, v: unit(dir(l1)) }, { l: l2, v: unit(dir(l2)) }];
  return out;
}
