// Sample days: the frozen model's real labels on held-out research-home clips (web/public/data/sample-days.json, made by
// tools/export_web_fixtures.py), replayed in the browser with staged clock times. Nothing here is live or anyone's home.
import { newState, actions, today as computeToday } from "./core.js";

let cache = null;
export async function sampleDays() { return cache || (cache = await fetch("/data/sample-days.json").then((r) => r.json())); }

/**
 * Play a sample day. onFrame(t) gets the same payload both screens draw, after every label.
 * Returns { stop() }. seconds = how long the whole morning takes to play.
 */
export async function play(sid, onFrame, { seconds = 16, names = { parent: "Dad", caregiver: "Meera" }, loop = false } = {}) {
  const days = await sampleDays(), d = days[sid];
  const off = -new Date().getTimezoneOffset() * 60;
  const day0 = Math.floor((Date.now() / 1000 + off) / 86400) * 86400 - off;
  let timer = null, stopped = false;
  const run = () => {
    const s = newState();
    actions.consent(s, day0 + d.started);
    const evs = [];
    let i = 0;
    const step = () => {
      if (stopped) return;
      const e = d.events[i];
      evs.push({ ...e, start: day0 + e.start, end: day0 + e.end });
      s.last_window_t = day0 + e.end;
      s.pauses = (d.pauses || []).filter((p) => p[1] <= e.end).map((p) => [day0 + p[0], day0 + p[1]]);   // "Dad paused it"
      const t = computeToday(s, evs, day0 + e.end + 1, { theta: 0.66, off, day0, hop: 2, names });
      t.sample = { id: sid, title: d.title, i: i + 1, n: d.events.length };
      onFrame(t);
      i++;
      if (i < d.events.length) timer = setTimeout(step, (seconds * 1000) / d.events.length);
      else if (loop) timer = setTimeout(run, 4000);
    };
    step();
  };
  run();
  return { stop() { stopped = true; clearTimeout(timer); } };
}
