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


if __name__ == "__main__":
    main()
