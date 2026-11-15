"""Writes web/public/desed-attribution.txt: the uploader of every DESED public-eval clip that Kettle scored.

DESED's own license_public_eval.tsv lists uploader and licence per clip. Run after `python -m eval.other_homes`
has produced results/other_homes_predictions.jsonl and data/raw/desed has been fetched.
"""
import csv, json, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
used = sorted({json.loads(l)["file"] for l in open(ROOT / "results/other_homes_predictions.jsonl") if json.loads(l)["set"] == "desed"})
lic = {r["filename"]: r for r in csv.DictReader(open(ROOT / "data/raw/desed/license_public_eval.tsv"), delimiter="\t")}
listed = [f for f in used if f in lic and lic[f]["license"]]
by = collections.Counter(lic[f]["license"] for f in listed)
lines = [
    "Kettle: attribution for DESED public-eval clips",
    "",
    "Kettle scored these clips to test itself on other people's homes. It was not trained on them and the project stores none of their audio.",
    "Source: DESED public evaluation set (Turpault, Serizel, Shah, Salamon), https://doi.org/10.5281/zenodo.3588172",
    "Uploader and licence are copied from the dataset's own license_public_eval.tsv. File names are <YouTube video id>_<start second>_<end second>.wav.",
    f"Clips scored: {len(used)}. With a licence entry in the dataset: {len(listed)} ({', '.join(f'{n} {k}' for k, n in by.items())}). No licence entry: {len(used) - len(listed)}, not listed below.",
    "",
    "file\tuploader\tlicence",
]
lines += [f"{f}\t{lic[f]['uploader']}\t{lic[f]['license']}" for f in listed]
out = ROOT / "web/public/desed-attribution.txt"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(out, len(used), len(listed), dict(by))
