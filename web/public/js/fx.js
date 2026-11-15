// Kettle motion helpers (landing). Hand-ported ideas, no code copied:
//  words()      split text into word spans for a staggered blur-in (Magic UI "text-animate" blurInUp; transitions.dev "Texts reveal" curve)
//  scrub()      scroll-linked word reveal, dim to full ink as you read (idea: React Bits "ScrollReveal", base opacity .16, blur 4px)
//  ticker()     count a number up with a damped spring when it scrolls into view (Magic UI "number-ticker": stiffness 100, damping 60)
//  progress()   0..1 position of an element through the viewport, for scroll-driven transforms
export const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));

export function words(root, cls = "w") {
  let i = 0;
  const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const texts = []; while (walk.nextNode()) texts.push(walk.currentNode);
  for (const t of texts) {
    const frag = document.createDocumentFragment();
    for (const part of t.textContent.split(/(\s+)/)) {
      if (!part) continue;
      if (/^\s+$/.test(part)) { frag.append(part); continue; }
      const s = document.createElement("span"); s.className = cls; s.style.setProperty("--i", i++); s.textContent = part; frag.append(s);
    }
    t.replaceWith(frag);
  }
  return [...root.querySelectorAll("." + cls)];
}

export function progress(el, start = 1, end = 0) {           // 0 when el's top is at start*vh, 1 when it is at end*vh
  const r = el.getBoundingClientRect(), vh = innerHeight;
  return clamp((start * vh - r.top) / ((start - end) * vh));
}

export function scrub(block, { base = 0.16, soft = 10 } = {}) {
  const ws = words(block, "sw");
  if (RM) { ws.forEach((w) => (w.style.opacity = 1)); return () => {}; }
  let last = -1;
  return () => {
    const p = progress(block, 0.88, 0.32), n = ws.length, head = p * (n + soft);
    if (Math.abs(head - last) < 0.05) return; last = head;
    ws.forEach((w, i) => { const o = (base + (1 - base) * clamp((head - i) / soft)).toFixed(2); if (w._o !== o) { w._o = o; w.style.opacity = o; } });   // opacity only: a per-word blur repainted the whole paragraph every frame
  };
}

export function ticker(node, to, { k = 100, c = 20 } = {}) {   // critically damped spring (Magic UI uses k100/c60, which crawls for 4 s on a 2-digit number; c20 settles in ~1 s), keeps the target's decimals
  const dec = (String(to).split(".")[1] || "").length, target = parseFloat(to);
  if (RM || !isFinite(target)) { node.textContent = to; return; }
  let x = 0, v = 0, t0 = null;
  const step = (t) => {
    const dt = t0 == null ? 1 / 60 : Math.min(0.05, (t - t0) / 1000); t0 = t;
    for (let s = 0; s < 4; s++) { const a = -k * (x - target) - c * v; v += a * dt / 4; x += v * dt / 4; }
    const done = Math.abs(x - target) < Math.pow(10, -dec) / 2 && Math.abs(v) < 0.05;
    node.textContent = (done ? target : x).toFixed(dec);
    if (!done) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

export function onScrollFrame(fn) {                              // one rAF per scroll burst, plus once now and on resize
  let raf = 0; const go = () => { raf = 0; fn(); };
  const req = () => { if (!raf) raf = requestAnimationFrame(go); };
  addEventListener("scroll", req, { passive: true }); addEventListener("resize", req); go();
}
