// Browser side of Web Push. Call subscribe() only from a user tap.

function b64uToBytes(s) {
  const p = s.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(p + "=".repeat((4 - (p.length % 4)) % 4));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

export function pushSupport() {
  const ua = navigator.userAgent || "";
  const ios = /iPhone|iPad|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const standalone = !!navigator.standalone || (window.matchMedia && matchMedia("(display-mode: standalone)").matches);
  const out = (why) => ({ ok: why === null, why, ios, standalone });
  if (!("serviceWorker" in navigator)) return out(ios && !standalone ? "ios-needs-home-screen" : "no-sw");
  if (ios && !standalone) return out("ios-needs-home-screen");
  if (!("PushManager" in window) || !("Notification" in window)) return out("no-push");
  if (Notification.permission === "denied") return out("denied");
  return out(null);
}

export async function registerSW() {
  try {
    if (!("serviceWorker" in navigator)) return null;
    return await navigator.serviceWorker.register("/sw.js", { scope: "/" });
  } catch {
    return null;
  }
}

export async function subscribe(vapidPublicKey) {
  const s = pushSupport();
  if (s.why === "ios-needs-home-screen") throw new Error("On iPhone, add Kettle to your Home Screen first (Share, then Add to Home Screen), then open it from there.");
  if (s.why === "denied") throw new Error("Notifications are blocked for this site. Allow them in your browser settings, then try again.");
  if (!s.ok) throw new Error("This browser can't receive alerts. Try Chrome, Edge, Firefox, or Safari on a Home Screen app.");
  const perm = await Notification.requestPermission();
  if (perm !== "granted") throw new Error("Alerts were not allowed. You can turn them on in your browser settings.");
  const reg = (await registerSW()) || null;
  if (!reg) throw new Error("Couldn't start the background helper. Reload the page and try again.");
  await navigator.serviceWorker.ready;
  try {
    const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64uToBytes(vapidPublicKey) });
    return sub.toJSON();
  } catch {
    throw new Error("Couldn't turn on alerts on this device. Check your connection and try again.");
  }
}

export async function currentSubscription() {
  try {
    if (!("serviceWorker" in navigator)) return null;
    const reg = await navigator.serviceWorker.getRegistration("/");
    const sub = reg && (await reg.pushManager.getSubscription());
    return sub ? sub.toJSON() : null;
  } catch {
    return null;
  }
}

export async function unsubscribe() {
  try {
    const reg = await navigator.serviceWorker.getRegistration("/");
    const sub = reg && (await reg.pushManager.getSubscription());
    return sub ? await sub.unsubscribe() : false;
  } catch {
    return false;
  }
}
