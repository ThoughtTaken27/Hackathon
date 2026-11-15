// Kettle app chrome (classic script, every app page): the sky behind the header, the nav that frosts on scroll, a gentle parallax.
// One sky everywhere (the landing hero's). data-scene still tracks the hour for anything that wants it; the family view passes the parent's hour.
(() => {
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const sky = document.createElement("div");
  sky.className = "sky"; sky.setAttribute("aria-hidden", "true");
  const pick = (h) => (h >= 5 && h < 11 ? "morning" : h >= 11 && h < 17 ? "day" : h >= 17 && h < 21 ? "dusk" : "night");
  let fixed = false;
  window.kettleSky = (h) => { fixed = true; const s = pick(h); if (sky.dataset.scene !== s) sky.dataset.scene = s; };
  sky.dataset.scene = pick(new Date().getHours());
  setInterval(() => { if (!fixed) sky.dataset.scene = pick(new Date().getHours()); }, 5 * 60 * 1000);
  const mount = () => {
    document.body.prepend(sky);
    const nav = document.querySelector(".nav");
    let raf = 0;
    const frame = () => {
      raf = 0;
      const y = scrollY;
      if (nav) nav.classList.toggle("solid", y > 8);
      if (!RM && y < 900) sky.style.setProperty("--sky-y", `${(y * 0.3).toFixed(1)}px`);
    };
    addEventListener("scroll", () => { if (!raf) raf = requestAnimationFrame(frame); }, { passive: true });
    frame();
  };
  if (document.body) mount(); else addEventListener("DOMContentLoaded", mount);
})();
