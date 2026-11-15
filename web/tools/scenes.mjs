// Generates Kettle's atmospheric scenes (layered misty ridges at dawn) as small SVG files. Original artwork, no photos.
//   node web/tools/scenes.mjs   -> web/public/img/scene-*.svg
import { writeFileSync, mkdirSync } from "node:fs";

function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
function noise1d(r, n) {                       // smooth value noise: random knots, cosine interpolation, several octaves
  const oct = [[1, 3], [0.5, 7], [0.25, 15], [0.12, 33], [0.06, 70]].map(([a, k]) => ({ a, k: Array.from({ length: k + 2 }, r) }));
  return Array.from({ length: n }, (_, i) => {
    const x = i / (n - 1); let v = 0;
    for (const { a, k } of oct) { const p = x * (k.length - 2), j = Math.floor(p), t = (1 - Math.cos((p - j) * Math.PI)) / 2; v += a * (k[j] * (1 - t) + k[j + 1] * t); }
    return v / 1.93;
  });
}
const mix = (a, b, t) => { const h = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16)); const A = h(a), B = h(b);
  return "#" + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, "0")).join(""); };

function scene({ seed, w = 2400, h = 1400, sky, far, near, fog, sun = null, layers = 6, base = 0.42, spread = 0.5, amp = 0.2, grain = 0.06 }) {
  const r = rng(seed), N = 220;
  let defs = `<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">${sky.map((c, i) => `<stop offset="${(i / (sky.length - 1)).toFixed(2)}" stop-color="${c}"/>`).join("")}</linearGradient>`;
  defs += `<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="${seed}" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5 0 0 0 0 .5 0 0 0 0 .5 0 0 0 ${grain} 0"/></filter>`;
  let body = `<rect width="${w}" height="${h}" fill="url(#sky)"/>`;
  if (sun) {
    defs += `<radialGradient id="sun" cx="${sun.x}" cy="${sun.y}" r="${sun.r}"><stop offset="0" stop-color="${sun.c}" stop-opacity=".85"/><stop offset=".35" stop-color="${sun.c}" stop-opacity=".28"/><stop offset="1" stop-color="${sun.c}" stop-opacity="0"/></radialGradient>`;
    body += `<rect width="${w}" height="${h}" fill="url(#sun)"/>`;
  }
  for (let L = 0; L < layers; L++) {
    const t = L / (layers - 1), n = noise1d(r, N);
    const y0 = h * (base + spread * t), a = h * amp * (1.1 + 0.9 * t);
    const pts = n.map((v, i) => `${((i / (N - 1)) * (w + 40) - 20).toFixed(1)},${(y0 - v * a).toFixed(1)}`);
    const top = mix(far, near, t), bot = mix(far, near, Math.min(1, t + 0.18));
    defs += `<linearGradient id="g${L}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${top}"/><stop offset="1" stop-color="${bot}"/></linearGradient>`;
    const blur = (1 - t) * 5;
    if (blur > 0.5) defs += `<filter id="b${L}" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="${blur.toFixed(1)}"/></filter>`;
    body += `<path d="M-20,${h + 20} L${pts.join(" L")} L${w + 20},${h + 20} Z" fill="url(#g${L})"${blur > 0.5 ? ` filter="url(#b${L})"` : ""}/>`;
    if (L < layers - 1) {                         // haze settling in each valley
      defs += `<linearGradient id="f${L}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${fog}" stop-opacity="0"/><stop offset=".6" stop-color="${fog}" stop-opacity="${(0.62 - 0.4 * t).toFixed(2)}"/><stop offset="1" stop-color="${fog}" stop-opacity="0"/></linearGradient>`;
      body += `<rect x="0" y="${(y0 - a * 0.45).toFixed(0)}" width="${w}" height="${(h * 0.3).toFixed(0)}" fill="url(#f${L})"/>`;
    }
  }
  body += `<rect width="${w}" height="${h}" filter="url(#grain)" opacity="1"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid slice"><defs>${defs}</defs>${body}</svg>`;
}

const S = {
  // hero: blue hour before dawn, the house still asleep
  hero: { seed: 11, sky: ["#1c2230", "#3d4757", "#7b8493", "#a7adb5"], far: "#8a929e", near: "#0c0e12", fog: "#b9c0c8", sun: { x: ".62", y: ".55", r: ".45", c: "#d9d2c8" }, layers: 5, base: 0.5, spread: 0.46, amp: 0.2 },
  // morning: first light, warm sky over teal hills
  morning: { seed: 23, sky: ["#efc0ae", "#f4d3c0", "#efe2d6"], far: "#b3c9c5", near: "#4e6f69", fog: "#f6e5da", sun: { x: ".3", y: ".42", r: ".5", c: "#fff1e4" }, layers: 5, base: 0.36, spread: 0.6, amp: 0.24 },
  // day: cool, clear, misty teal
  day: { seed: 37, sky: ["#d9dfdc", "#c6d3d0", "#b5c7c4"], far: "#a9c0bd", near: "#507069", fog: "#e2ebe8", sun: { x: ".75", y: ".3", r: ".5", c: "#ffffff" }, layers: 5, base: 0.32, spread: 0.62, amp: 0.26 },
  // home: a clear, soft morning; pale sky so dark text reads on it, sage hills low in the frame (light theme, Nov 15)
  home: { seed: 29, sky: ["#e9eff1", "#f1f2ef", "#f6f1ea"], far: "#cbd8d2", near: "#56766c", fog: "#f5f2ec", sun: { x: ".7", y: ".5", r: ".5", c: "#fff7ec" }, layers: 5, base: 0.56, spread: 0.4, amp: 0.16 },
  // dusk: the kitchen light on, the day done
  dusk: { seed: 53, sky: ["#14161d", "#2c2a38", "#5d4f5b", "#9a7b74"], far: "#6c6170", near: "#0a0b0e", fog: "#a68d84", sun: { x: ".5", y: ".62", r: ".4", c: "#f2b88c" }, layers: 5, base: 0.56, spread: 0.4, amp: 0.18 },
};
const out = new URL("../public/img/", import.meta.url);
mkdirSync(out, { recursive: true });
for (const [k, v] of Object.entries(S)) {
  const svg = scene(v);
  writeFileSync(new URL(`scene-${k}.svg`, out), svg);
  console.log(`scene-${k}.svg ${(svg.length / 1024).toFixed(0)} KB`);
}
