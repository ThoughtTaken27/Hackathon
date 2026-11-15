"""The detection-accuracy results the How sure page shows, copied from results/*.json (never typed by hand).

    python tools/export_accuracy.py      writes web/public/data/accuracy.json from
    results/kitchen_naming.json (rules 2c/2d), results/sounds.json (named sounds), results/judge.json and results/confetti.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = lambda n: json.loads((ROOT / "results" / n).read_text())


def main() -> None:
    kn, so, ju, co = R("kitchen_naming.json"), R("sounds.json"), R("judge.json"), R("confetti.json")
    out = {"kitchen_naming": {k: {"n": v["n"], "before": v["before"], "after": v["after"]} for k, v in kn["sets"].items()},
           "kitchen_naming_process": kn["process"],
           "sounds": {"bar": so["bar"], "before": so["before"], "after": so["after"]},
           "judge": {"decision": ju["decision"], "dev": {t: v["_gate"] for t, v in ju["dev"].items()}},
           "confetti": {"decision": co["decision"], "variants": co["variants"]},
           "source": "tools/export_accuracy.py"}
    (ROOT / "web" / "public" / "data" / "accuracy.json").write_text(json.dumps(out))
    print("wrote web/public/data/accuracy.json")
    fill_writeup(out)


def fill_writeup(A: dict) -> None:
    """The live-kitchen accuracy story for docs/WRITEUP.md, between <!-- accuracy:start --> and <!-- accuracy:end -->."""
    import re
    K, S, J = A["kitchen_naming"], A["sounds"], A["judge"]["dev"]
    sd, kt, dt = K["sins_dev_sessions"], K["kitchen20_test"], K["desed_test"]
    pc = lambda r: f"{r['pct']:.1f}%"
    b, a = S["before"], S["after"]
    names = {k["id"]: k["name"] for k in json.loads((ROOT / "web" / "public" / "model" / "kinds.json").read_text())["kinds"]}
    shown = [k for k, v in a.items() if v["shown"]]
    j = J["0.9"]
    text = "\n".join([
        "| Change (Sun Nov 15, after a live test in a teammate's kitchen) | Before → after | N |",
        "|---|---|---|",
        f"| Kitchen stretch named from evidence across its windows (rules 2c, 2d): research home, right activity | {sd['before']['right']} → {sd['after']['right']} of {sd['before']['meal']} sessions | {sd['n']:,} sessions |",
        f"| Same, Kitchen20 test half: wrong activity | {kt['before']['wrong_activity']} → {kt['after']['wrong_activity']} of {kt['before']['meal']} clips | {kt['n']:,} clips |",
        f"| Same, DESED homes test half: dish clatter called washing up or eating | {dt['before']['dishes_called_washing_or_eating']} → {dt['after']['dishes_called_washing_or_eating']} of {dt['before']['dishes']} | {dt['n']:,} clips |",
        f"| Named sound \"kettle\": precision (false names per 1,000 windows) | {pc(b['kettle']['precision'])} ({b['kettle']['false_per_1000']}) → {pc(a['kettle']['precision'])} ({a['kettle']['false_per_1000']}) | {a['kettle']['recall']['n']} kettle clips |",
        f"| Named sound \"running water\": precision (false names per 1,000 windows) | {pc(b['tap']['precision'])} ({b['tap']['false_per_1000']}) → {pc(a['tap']['precision'])} ({a['tap']['false_per_1000']}) | {a['tap']['recall']['n']} tap clips |",
        f"| Sound names that passed the pre-registered bar (precision ≥ {S['bar']['precision']:.0f}%, recall ≥ {S['bar']['recall']:.0f}%) | {len(shown)} of {len(a)}: {', '.join(names[k] for k in shown)} ({pc(a[shown[0]]['precision'])} precision, {pc(a[shown[0]]['recall'])} recall); the rest are hidden | test halves |",
        f"| Not shipped: a trained judge on the 527 tags (strictest cutoff) | wrong activity {j['wrong_activity'][0]} → {j['wrong_activity'][1]}, but right {j['right'][0]} → {j['right'][1]}: failed the gate written before the run | development, out-of-fold |",
    ])
    p = ROOT / "docs" / "WRITEUP.md"
    t = p.read_text()
    if "<!-- accuracy:start -->" in t:
        p.write_text(re.sub(r"<!-- accuracy:start -->.*?<!-- accuracy:end -->", f"<!-- accuracy:start -->\n{text}\n<!-- accuracy:end -->", t, flags=re.S))
        print("filled docs/WRITEUP.md accuracy block")


if __name__ == "__main__":
    main()
