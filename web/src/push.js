// Web Push for Kettle: VAPID (RFC 8292) + aes128gcm message encryption (RFC 8291/8188).
// Runs in Cloudflare Workers and Node 22: WebCrypto, TextEncoder, fetch, btoa/atob only.

const enc = new TextEncoder();
const PUSH_HOSTS = [
  "fcm.googleapis.com", "updates.push.services.mozilla.com", "push.services.mozilla.com",
  "web.push.apple.com", "notify.windows.com", "push.apple.com",
];

export function b64uEncode(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64uDecode(str) {
  const s = String(str).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(s + "=".repeat((4 - (s.length % 4)) % 4));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function concat(...parts) {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}

const subtle = () => globalThis.crypto.subtle;

/** Generate a VAPID key pair once; the caller stores it. */
export async function makeVapidKeys() {
  const pair = await subtle().generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const pub = new Uint8Array(await subtle().exportKey("raw", pair.publicKey));
  const privateJwk = await subtle().exportKey("jwk", pair.privateKey);
  return { publicKey: b64uEncode(pub), privateJwk };
}

/** Build the VAPID Authorization header for one push endpoint. */
export async function vapidHeaders(endpoint, keys, subject = "mailto:kettle@example.invalid", now = Date.now() / 1000) {
  const aud = new URL(endpoint).origin;
  const header = b64uEncode(enc.encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const claims = b64uEncode(enc.encode(JSON.stringify({ aud, exp: Math.floor(now) + 12 * 3600, sub: subject })));
  const key = await subtle().importKey("jwk", keys.privateJwk, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const sig = new Uint8Array(await subtle().sign({ name: "ECDSA", hash: "SHA-256" }, key, enc.encode(`${header}.${claims}`)));
  return { Authorization: `vapid t=${header}.${claims}.${b64uEncode(sig)}, k=${keys.publicKey}` };
}

async function hkdf(salt, ikm, info, bytes) {
  const k = await subtle().importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await subtle().deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, k, bytes * 8));
}

/** Encrypt payloadBytes for a subscription into an aes128gcm body. salt/asPrivateKey (JWK) are for tests only. */
export async function encryptPayload(subscription, payloadBytes, { salt, asPrivateKey } = {}) {
  const uaPublic = b64uDecode(subscription.keys.p256dh);
  const authSecret = b64uDecode(subscription.keys.auth);
  if (payloadBytes.length > 4096 - 16 - 1) throw new Error("payload too large");

  let asPriv, asPublic;
  if (asPrivateKey) {
    asPriv = await subtle().importKey("jwk", { ...asPrivateKey, key_ops: undefined, ext: true }, { name: "ECDH", namedCurve: "P-256" }, false, ["deriveBits"]);
    asPublic = concat(new Uint8Array([4]), b64uDecode(asPrivateKey.x), b64uDecode(asPrivateKey.y));
  } else {
    const pair = await subtle().generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
    asPriv = pair.privateKey;
    asPublic = new Uint8Array(await subtle().exportKey("raw", pair.publicKey));
  }
  const uaKey = await subtle().importKey("raw", uaPublic, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const ecdh = new Uint8Array(await subtle().deriveBits({ name: "ECDH", public: uaKey }, asPriv, 256));

  const s = salt || globalThis.crypto.getRandomValues(new Uint8Array(16));
  const keyInfo = concat(enc.encode("WebPush: info\0"), uaPublic, asPublic);
  const ikm = await hkdf(authSecret, ecdh, keyInfo, 32);
  const cek = await hkdf(s, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(s, ikm, enc.encode("Content-Encoding: nonce\0"), 12);

  const record = concat(payloadBytes, new Uint8Array([2]));
  const aes = await subtle().importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const cipher = new Uint8Array(await subtle().encrypt({ name: "AES-GCM", iv: nonce }, aes, record));

  const rs = new Uint8Array(4);
  new DataView(rs.buffer).setUint32(0, 4096);
  return concat(s, rs, new Uint8Array([asPublic.length]), asPublic, cipher);
}

/** Send one push. Never throws. gone=true means the subscription is dead and should be deleted. */
export async function sendPush(subscription, payloadObj, keys, { ttl = 3600, urgency = "high", fetchImpl = fetch } = {}) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 8000);
  try {
    const body = await encryptPayload(subscription, enc.encode(JSON.stringify(payloadObj)));
    const auth = await vapidHeaders(subscription.endpoint, keys);
    const res = await fetchImpl(subscription.endpoint, {
      method: "POST",
      headers: {
        ...auth,
        "Content-Encoding": "aes128gcm",
        "Content-Type": "application/octet-stream",
        TTL: String(ttl),
        Urgency: urgency,
      },
      body,
      signal: ctl.signal,
    });
    return { ok: res.status >= 200 && res.status < 300, status: res.status, gone: res.status === 404 || res.status === 410 };
  } catch {
    return { ok: false, status: 0, gone: false };
  } finally {
    clearTimeout(timer);
  }
}

/** Return a cleaned subscription, or null if it could be abused or is malformed. */
export function validSubscription(sub) {
  try {
    if (!sub || typeof sub.endpoint !== "string" || sub.endpoint.length > 1024) return null;
    const url = new URL(sub.endpoint);
    if (url.protocol !== "https:") return null;
    const host = url.hostname.toLowerCase();
    if (!PUSH_HOSTS.some((h) => host === h || host.endsWith("." + h))) return null;
    const p256dh = sub.keys && sub.keys.p256dh;
    const auth = sub.keys && sub.keys.auth;
    if (typeof p256dh !== "string" || typeof auth !== "string") return null;
    const pk = b64uDecode(p256dh);
    if (pk.length !== 65 || pk[0] !== 4) return null;
    if (b64uDecode(auth).length !== 16) return null;
    return { endpoint: sub.endpoint, keys: { p256dh, auth } };
  } catch {
    return null;
  }
}
