"""Translation batches: split -> agents translate -> check -> merge; pairs files for reviewers.

    python -X utf8 tools/batches.py split b01          # work/tl/b01.tsv + work/tl/terms_b01.txt
    python -X utf8 tools/batches.py check b01          # validates work/tl/b01.out.tsv, prints OK or errors
    python -X utf8 tools/batches.py merge b01          # check, then write "en" into script/*.json
    python -X utf8 tools/batches.py pairs b01          # work/tl/b01.pairs.txt for the reviewer
    python -X utf8 tools/batches.py lint               # every non-empty "en" in script/ (build gate)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TL = ROOT / "work" / "tl"
FILES = [ROOT / "script" / "messages.json", ROOT / "script" / "substrings.json", ROOT / "script" / "other.json"]


def rng(a, b):
    return [f"M{i:03X}" for i in range(a, b + 1)]


BATCHES = {
    "b01": rng(0x06, 0x1D) + rng(0x20, 0x63) + ["M0ED"] + rng(0x105, 0x108) + rng(0x110, 0x11B),
    "pilot": rng(0x70, 0x7F),
    "b02": rng(0x80, 0xAF),
    "b03": rng(0xB0, 0xF7) + rng(0x100, 0x101) + rng(0x103, 0x104),
    "special": ["M003", "M004", "M005", "M01E", "M01F"] + rng(0x64, 0x6F) + ["M0F8", "M0F9", "M102"],
    "subs": [f"S{i:03X}" for i in range(64)],
    "credits": ["M0FA", "M0FB"] + rng(0x11C, 0x127),
    "other": [f"B{i:02X}" for i in range(23)] + [f"T{i:02X}" for i in range(1, 6)] + ["P00"],
}
CTRL = re.compile(r"\{[^}]*\}")


def load():
    entries = []
    for f in FILES:
        entries += json.loads(f.read_text(encoding="utf-8"))
    return entries


def save(entries):
    by_file = {f: [] for f in FILES}
    for e in entries:
        by_file[FILES[{"M": 0, "S": 1}.get(e["id"][0], 2)]].append(e)
    for f, es in by_file.items():
        f.write_text(json.dumps(es, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def batch_entries(name):
    ids = set(BATCHES[name])
    return [e for e in load() if e["id"] in ids and "same_as" not in e]


def glossary():
    """[(jp, en_options, avoid)] from glossary.md table rows."""
    rows = []
    for line in (ROOT / "glossary.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not line.startswith("|") or cells[0] in ("JP", "---") or cells[0].startswith("-"):
            continue
        jps, ens = [j.strip() for j in cells[0].split(" / ")], [e.strip() for e in cells[1].split(" / ")]
        avoid = [a.strip() for a in cells[3].split(",")] if len(cells) > 3 and cells[3] else []
        if ens[0].startswith("("):
            continue
        for i, jp in enumerate(jps):
            en = ens[i] if len(ens) == len(jps) else ens
            rows.append((jp, [en] if isinstance(en, str) else en, [a for a in avoid if a]))
    return rows


def norm(s):
    return re.sub(r"^the ", "", s, flags=re.I).lower()


def check_entry(mid, jp, en, terms):
    errs = []
    if any(ord(c) > 0x7E or ord(c) < 0x20 for c in en if c not in "↓↘→↙←↑　０"):
        errs.append(f"{mid}: non-ASCII/control character")
    if "\\u" in en or "\t" in en:
        errs.append(f"{mid}: escape or tab")
    a = Counter(c for c in CTRL.findall(jp) if c not in ("{n}", "{end}"))
    b = Counter(c for c in CTRL.findall(en) if c not in ("{n}", "{end}"))
    if a != b:
        errs.append(f"{mid}: control codes differ: jp {dict(a)} en {dict(b)}")
    if re.search(r"\{(name|var|sub)\w*\}(st|nd|rd|th)\b", en):
        errs.append(f"{mid}: ordinal suffix after a variable")
    _, werrs = fit.wrap(en, mid)
    errs += werrs
    low = en.lower()
    rest = "" if mid in BATCHES["credits"] else jp    # credits: cast rows hold short names; drawn with another font
    for tj, ten, avoid in sorted(terms, key=lambda t: -len(t[0])):   # longest first: 霊界たんてい before 霊界
        if tj in rest:
            rest = rest.replace(tj, "\0")
            if not any(norm(t) in low for t in ten):
                errs.append(f"{mid}: glossary: {tj} -> {' / '.join(ten)}")
        for av in avoid:
            if re.search(rf"\b{re.escape(av.lower())}\b", low):
                errs.append(f"{mid}: avoid {av!r}")
    return errs


def split(name):
    TL.mkdir(parents=True, exist_ok=True)
    es = batch_entries(name)
    lines = []
    for e in es:
        f = fit.form(e["id"])
        w, n = fit.BOXES[f]
        jp = e["jp"].replace("{end}", "").replace("{n}", " / ")
        lines.append(f"{e['id']}\t{f}\t{n} lines x {w}px\t{jp}")
    (TL / f"{name}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    text = "".join(e["jp"] for e in es)
    rows = [f"{jp}\t{' / '.join(en)}" for jp, en, _ in glossary() if jp in text]
    (TL / f"terms_{name}.txt").write_text("\n".join(dict.fromkeys(rows)) + "\n", encoding="utf-8", newline="\n")
    print(f"{name}: {len(es)} entries, {len(text)} JP chars -> {TL / (name + '.tsv')}")


def read_out(name):
    out = {}
    for line in (TL / f"{name}.out.tsv").read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        mid, _, en = line.partition("\t")
        if mid in out:
            raise SystemExit(f"duplicate id {mid}")
        out[mid] = en.strip()
    return out


def check(name):
    es = batch_entries(name)
    out = read_out(name)
    errs = []
    want = {e["id"] for e in es}
    if set(out) != want:
        errs.append(f"ids: missing {sorted(want - set(out))} extra {sorted(set(out) - want)}")
    terms = glossary()
    for e in es:
        if e["id"] in out:
            errs += check_entry(e["id"], e["jp"], out[e["id"]], terms)
    print("\n".join(errs) or "OK")
    return not errs


def merge(name):
    if not check(name):
        sys.exit(1)
    out = read_out(name)
    entries = load()
    for e in entries:
        if e["id"] in out:
            e["en"] = out[e["id"]]
    save(entries)
    print(f"merged {len(out)} entries")


def pairs(name):
    es = load()
    idx = {e["id"]: i for i, e in enumerate(es)}
    want = [e["id"] for e in batch_entries(name)]
    out = []
    for mid in want:
        i = idx[mid]
        for j in range(max(0, i - 2), min(len(es), i + 3)):
            e = es[j]
            mark = ">>" if j == i else "  "
            out.append(f"{mark} {e['id']} | {e['jp'].replace('{end}', '')}\n   {'':4} | {e.get('en', '')}")
        out.append("")
    (TL / f"{name}.pairs.txt").write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(TL / f"{name}.pairs.txt")


def lint():
    terms = glossary()
    errs = []
    for e in load():
        if e.get("en"):
            errs += check_entry(e["id"], e["jp"], e["en"], terms)
    print("\n".join(errs) or "lint OK")
    return not errs


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "lint":
        sys.exit(0 if lint() else 1)
    {"split": split, "check": lambda n: sys.exit(0 if check(n) else 1), "merge": merge, "pairs": pairs}[cmd](sys.argv[2])
