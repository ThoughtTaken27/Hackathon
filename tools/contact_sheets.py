"""Contact sheets for a screenshot round: every capture of two states per sheet (desktop light/dark, phone light/dark).

Lets a reviewer open every screenshot of a round at a glance, then open full-size files where something looks off.
Usage: python tools/contact_sheets.py <round>   -> docs/screenshots/round-<n>/sheets/sheet-XX.png
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
H = 360          # row height in px
GAP = 12


def main(rnd: str) -> None:
    d = ROOT / "docs" / "screenshots" / f"round-{rnd}"
    out = d / "sheets"
    out.mkdir(exist_ok=True)
    states = sorted({p.name.rsplit("-", 2)[0] for p in d.glob("*.png")})
    order = ["desktop-light", "desktop-dark", "phone-light", "phone-dark"]
    rows = []
    for s in states:
        ims = []
        for o in order:
            p = d / f"{s}-{o}.png"
            if p.exists():
                im = Image.open(p).convert("RGB")
                if im.height > im.width * 1.4 and "desktop" in o:      # full-page captures: keep the top
                    im = im.crop((0, 0, im.width, int(im.width * 0.625)))
                if "phone" in o and im.height > im.width * 2.4:
                    im = im.crop((0, 0, im.width, int(im.width * 2.17)))
                im = im.resize((max(1, int(im.width * H / im.height)), H))
                ims.append(im)
        rows.append((s, ims))
    for i in range(0, len(rows), 2):
        pair = rows[i:i + 2]
        w = max(sum(im.width for im in ims) + GAP * (len(ims) + 1) for _, ims in pair)
        sheet = Image.new("RGB", (w, len(pair) * (H + 34 + GAP) + GAP), (200, 204, 210))
        dr = ImageDraw.Draw(sheet)
        y = GAP
        for name, ims in pair:
            dr.text((GAP, y), name, fill=(10, 10, 10))
            x = GAP
            for im in ims:
                sheet.paste(im, (x, y + 22))
                x += im.width + GAP
            y += H + 34 + GAP
        sheet.save(out / f"sheet-{i // 2 + 1:02d}.png")
    print(f"{(len(rows) + 1) // 2} sheets for {len(rows)} states -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
