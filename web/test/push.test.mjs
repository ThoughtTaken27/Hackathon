import { test } from "node:test";
import assert from "node:assert/strict";
import { makeVapidKeys, vapidHeaders, encryptPayload, sendPush, validSubscription, b64uEncode, b64uDecode } from "../src/push.js";

const subtle = globalThis.crypto.subtle;
const enc = new TextEncoder();
const cat = (...p) => { const o = new Uint8Array(p.reduce((n, x) => n + x.length, 0)); let i = 0; for (const x of p) { o.set(x, i); i += x.length; } return o; };

async function hkdf(salt, ikm, info, n) {
  const k = await subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, k, n * 8));
}

// Receiver side (user agent) decrypt, written independently of push.js.
async function decrypt(body, uaPrivJwk, uaPublic, auth) {
  const salt = body.slice(0, 16);
  const idlen = body[20];
  const asPublic = body.slice(21, 21 + idlen);
  const cipher = body.slice(21 + idlen);
  const priv = await subtle.importKey("jwk", uaPrivJwk, { name: "ECDH", namedCurve: "P-256" }, false, ["deriveBits"]);
  const asKey = await subtle.importKey("raw", asPublic, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const ecdh = new Uint8Array(await subtle.deriveBits({ name: "ECDH", public: asKey }, priv, 256));
  const ikm = await hkdf(auth, ecdh, cat(enc.encode("WebPush: info\0"), uaPublic, asPublic), 32);
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);
  const key = await subtle.importKey("raw", cek, "AES-GCM", false, ["decrypt"]);
  const plain = new Uint8Array(await subtle.decrypt({ name: "AES-GCM", iv: nonce }, key, cipher));
  assert.equal(plain[plain.length - 1], 2, "padding delimiter");
  return plain.slice(0, -1);
}

async function freshReceiver() {
  const pair = await subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const pub = new Uint8Array(await subtle.exportKey("raw", pair.publicKey));
  const jwk = await subtle.exportKey("jwk", pair.privateKey);
  const auth = globalThis.crypto.getRandomValues(new Uint8Array(16));
  return { pub, jwk, auth, sub: { endpoint: "https://fcm.googleapis.com/fcm/send/abc", keys: { p256dh: b64uEncode(pub), auth: b64uEncode(auth) } } };
}

test("RFC 8291 appendix A vector reproduced exactly", async () => {
  const asPublic = b64uDecode("BP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A8");
  const asPrivateKey = { kty: "EC", crv: "P-256", d: "yfWPiYE-n46HLnH0KqZOF1fJJU3MYrct3AELtAQ-oRw", x: b64uEncode(asPublic.slice(1, 33)), y: b64uEncode(asPublic.slice(33)) };
  const sub = {
    endpoint: "https://push.example.net/push/JzLQ3raZJfFBR0aqvOMsLrt54w4rJUsV",
    keys: { p256dh: "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4", auth: "BTBZMqHH6r4Tts7J_aSIgg" },
  };
  const body = await encryptPayload(sub, enc.encode("When I grow up, I want to be a watermelon"), { salt: b64uDecode("DGv6ra1nlYgDCS1FRnbzlw"), asPrivateKey });
  const header = "DGv6ra1nlYgDCS1FRnbzlwAAEABBBP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK6PBru3jl7A8";
  const cipher = "8pfeW0KbunFT06SuDKoJH9Ql87S1QUrdirN6GcG7sFz1y1sqLgVi1VhjVkHsUoEsbI_0LpXMuGvnzQ";
  assert.deepEqual(body, cat(b64uDecode(header), b64uDecode(cipher)));
});

test("round trip with a fresh receiver", async () => {
  const r = await freshReceiver();
  const payload = globalThis.crypto.getRandomValues(new Uint8Array(500));
  const body = await encryptPayload(r.sub, payload);
  assert.equal(body[20], 65);
  assert.deepEqual([...body.slice(16, 20)], [0, 0, 0x10, 0]);
  assert.deepEqual(await decrypt(body, r.jwk, r.pub, r.auth), payload);
});

test("vapid JWT verifies and has aud/exp/sub", async () => {
  const keys = await makeVapidKeys();
  assert.equal(b64uDecode(keys.publicKey).length, 65);
  const now = 1_700_000_000;
  const h = await vapidHeaders("https://fcm.googleapis.com/fcm/send/xyz", keys, "mailto:a@b.co", now);
  const m = /^vapid t=([^,]+), k=(.+)$/.exec(h.Authorization);
  assert.ok(m);
  assert.equal(m[2], keys.publicKey);
  const [hd, cl, sg] = m[1].split(".");
  assert.deepEqual(JSON.parse(new TextDecoder().decode(b64uDecode(hd))), { typ: "JWT", alg: "ES256" });
  assert.deepEqual(JSON.parse(new TextDecoder().decode(b64uDecode(cl))), { aud: "https://fcm.googleapis.com", exp: now + 43200, sub: "mailto:a@b.co" });
  const sig = b64uDecode(sg);
  assert.equal(sig.length, 64);
  const pub = await subtle.importKey("raw", b64uDecode(keys.publicKey), { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
  assert.ok(await subtle.verify({ name: "ECDSA", hash: "SHA-256" }, pub, sig, enc.encode(`${hd}.${cl}`)));
});

test("validSubscription accepts good, rejects bad", async () => {
  const r = await freshReceiver();
  const ok = validSubscription({ ...r.sub, extra: 1 });
  assert.deepEqual(ok, { endpoint: r.sub.endpoint, keys: r.sub.keys });
  assert.equal(validSubscription({ ...r.sub, endpoint: "http://fcm.googleapis.com/x" }), null);
  assert.equal(validSubscription({ ...r.sub, endpoint: "https://evil.example.com/x" }), null);
  assert.equal(validSubscription({ ...r.sub, endpoint: "https://fcm.googleapis.com.evil.com/x" }), null);
  assert.equal(validSubscription({ ...r.sub, endpoint: "https://evilfcm.googleapis.com/" + "a".repeat(1100) }), null);
  assert.equal(validSubscription({ ...r.sub, keys: { ...r.sub.keys, p256dh: b64uEncode(r.pub.slice(0, 64)) } }), null);
  assert.equal(validSubscription({ ...r.sub, keys: { ...r.sub.keys, auth: b64uEncode(new Uint8Array(15)) } }), null);
  assert.equal(validSubscription({ ...r.sub, keys: { ...r.sub.keys, p256dh: b64uEncode(new Uint8Array(65)) } }), null);
  assert.equal(validSubscription(null), null);
  assert.equal(validSubscription({ endpoint: r.sub.endpoint }), null);
});

test("sendPush headers, gone on 410, no throw on network error", async () => {
  const r = await freshReceiver();
  const keys = await makeVapidKeys();
  let seen;
  const f = (status) => async (url, init) => { seen = { url, init }; return { status }; };
  const res = await sendPush(r.sub, { title: "t" }, keys, { ttl: 120, urgency: "normal", fetchImpl: f(201) });
  assert.deepEqual(res, { ok: true, status: 201, gone: false });
  assert.equal(seen.url, r.sub.endpoint);
  assert.equal(seen.init.method, "POST");
  const h = seen.init.headers;
  assert.equal(h["Content-Encoding"], "aes128gcm");
  assert.equal(h["Content-Type"], "application/octet-stream");
  assert.equal(h.TTL, "120");
  assert.equal(h.Urgency, "normal");
  assert.match(h.Authorization, /^vapid t=.+, k=.+$/);
  assert.deepEqual(JSON.parse(new TextDecoder().decode(await decrypt(seen.init.body, r.jwk, r.pub, r.auth))), { title: "t" });
  assert.deepEqual(await sendPush(r.sub, {}, keys, { fetchImpl: f(410) }), { ok: false, status: 410, gone: true });
  assert.equal((await sendPush(r.sub, {}, keys, { fetchImpl: f(404) })).gone, true);
  assert.equal((await sendPush(r.sub, {}, keys, { fetchImpl: f(500) })).gone, false);
  const boom = await sendPush(r.sub, {}, keys, { fetchImpl: async () => { throw new Error("net"); } });
  assert.equal(boom.ok, false);
});
