// String lint (plan 3.7): no gendered words and no hardcoded "Dad"/"Mom" in user-facing strings.
// Scans string literals in public/js/*.js and visible text in public/*.html.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";

const PUB = join(dirname(fileURLToPath(import.meta.url)), "../public");
// Files another engineer is rewriting right now. Remove a file from this list when it is done.
const PENDING = ["js/core.js", "js/kitchen.js", "js/family.js", "index.html"];
// Files where invented sample personas (Dad, Meera) are allowed to appear by name.
const PERSONA_OK = new Set(["js/people.js", "js/landing.js", "js/sample.js", "credits.html", "index.html"]);
// Files that quote datasets or research: gendered words in quoted text are allowed.
const QUOTE_OK = new Set(["credits.html", "how-sure.html", "js/howsure.js"]);

// Exact strings that may name Dad/Mom: the setup placeholder lists example names.
const NAME_EXAMPLES = /^For example Mom, Dad, /;
const GENDER = /\b(his|him|her|she|he)\b/i;
const NAMED = /\b(Dad|Mom)\b/;

// Tokenise JS: return [{line, text}] for each string literal and template text, skipping comments and regex-free code.
export function jsStrings(src) {
  const out = []; let i = 0, line = 1;
  while (i < src.length) {
    const c = src[i], n = src[i + 1];
    if (c === "\n") { line++; i++; continue; }
    if (c === "/" && n === "/") { while (i < src.length && src[i] !== "\n") i++; continue; }
    if (c === "/" && n === "*") { i += 2; while (i < src.length && !(src[i] === "*" && src[i + 1] === "/")) { if (src[i] === "\n") line++; i++; } i += 2; continue; }
    if (c === '"' || c === "'" || c === "`") {
      const q = c, start = line; let buf = ""; i++;
      while (i < src.length && src[i] !== q) {
        if (src[i] === "\\") { buf += src[i + 1]; i += 2; continue; }
        if (src[i] === "\n") line++;
        if (q === "`" && src[i] === "$" && src[i + 1] === "{") {
          let d = 1; i += 2;
          while (i < src.length && d) { if (src[i] === "{") d++; else if (src[i] === "}") d--; if (src[i] === "\n") line++; i++; }
          buf += " "; continue;
        }
        buf += src[i]; i++;
      }
      i++; out.push({ line: start, text: buf }); continue;
    }
    i++;
  }
  return out;
}

// Visible text of an HTML file: drop scripts, styles, comments and tags. Keeps line numbers.
export function htmlText(src) {
  const blank = (m) => m.replace(/[^\n]/g, " ");
  const t = src.replace(/<!--[\s\S]*?-->/g, blank).replace(/<(script|style)[\s\S]*?<\/\1>/gi, blank).replace(/<[^>]*>/g, blank);
  return t.split("\n").map((text, k) => ({ line: k + 1, text }));
}
const attrText = (src) => src.split("\n").flatMap((l, k) => [...l.matchAll(/\b(?:alt|title|aria-label|content|placeholder)="([^"]*)"/g)].map((m) => ({ line: k + 1, text: m[1] })));

function problems(rel, items) {
  const bad = [];
  for (const { line, text } of items) {
    if (!QUOTE_OK.has(rel) && GENDER.test(text)) bad.push(`${rel}:${line}  gendered word: ${text.trim().slice(0, 100)}`);
    if (!PERSONA_OK.has(rel) && !NAME_EXAMPLES.test(text.trim()) && NAMED.test(text)) bad.push(`${rel}:${line}  literal Dad/Mom: ${text.trim().slice(0, 100)}`);
  }
  return bad;
}

const files = [...readdirSync(PUB).filter((f) => f.endsWith(".html")), ...readdirSync(join(PUB, "js")).filter((f) => f.endsWith(".js")).map((f) => "js/" + f)];

test("tokenizer sanity", () => {
  assert.deepEqual(jsStrings('const a = "x his"; // she\n/* he */ const b = `y ${"z"} him`;').map((s) => s.text), ["x his", "y   him"]);
  assert.ok(htmlText("<p>her <b>x</b></p><script>var he='x'</script>").every((l) => !/he=/.test(l.text)));
});

for (const rel of files) {
  test(`words: ${rel}`, (t) => {
    if (PENDING.includes(rel)) return t.skip(`pending rewrite (${PENDING.join(", ")})`);
    const src = readFileSync(join(PUB, rel), "utf8");
    const items = rel.endsWith(".js") ? jsStrings(src) : [...htmlText(src), ...attrText(src)];
    if (rel.endsWith(".html")) for (const m of src.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) if (m[1].trim()) { const base = src.slice(0, m.index).split("\n").length - 1; items.push(...jsStrings(m[1]).map((s) => ({ ...s, line: s.line + base }))); }
    const bad = problems(rel, items);
    assert.equal(bad.length, 0, "\n" + bad.join("\n"));
  });
}
