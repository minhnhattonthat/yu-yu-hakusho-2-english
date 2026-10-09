"""Box limits and balanced word wrap for English text (VWF widths from tools/font.py).

    python -X utf8 tools/fit.py M070 "text to try"     # wrapped lines with pixel widths, errors
English in script/*.json is written as prose; the build wraps each page (pages split at {clr}/{wait}) to the
box width. {n} forces a break. Lines past the box's line count fail the check.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import font  # noqa: E402

_, WIDTHS, _ = font.build()
TOKEN = re.compile(r"(\{[^}]*\})")
NAME_W = 92                     # widest fighter name a {nameX} can print ("Shishiwakamaru")
# form: (px per line, lines per page)
BOXES = {"bubble": (176, 2), "quote": (176, 3), "story": (176, 5), "special": (None, None)}


def form(mid):
    n = int(mid[1:], 16)
    if mid[0] == "S":
        return "special"
    if 0x06 <= n <= 0x19 or 0x105 <= n <= 0x108:
        return "bubble"
    if 0x1A <= n <= 0x1D or 0x20 <= n <= 0x63 or n == 0xED or 0x110 <= n <= 0x11B:
        return "quote"
    if 0x70 <= n <= 0xF7 and n not in (0xF8, 0xF9, 0xFA, 0xFB) or 0x100 <= n <= 0x101 or 0x103 <= n <= 0x104:
        return "story"
    return "special"


def width(s):
    w = 0
    for part in TOKEN.split(s):
        if part.startswith("{"):
            w += NAME_W if part.startswith("{name") else 0
        else:
            w += sum(WIDTHS[ord(c) - 0x20] if 0x20 <= ord(c) < 0x7F else 16 for c in part)
    return w


def greedy(words, maxw):
    lines, cur = [], ""
    for wd in words:
        trial = f"{cur} {wd}" if cur else wd
        if cur and width(trial) > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def wrap_para(para, maxw):
    """Fewest lines, then the narrowest widest line (balanced)."""
    words = para.split()
    if not words:
        return [""]
    best = greedy(words, maxw)
    lo, hi = 1, maxw
    while lo < hi:
        mid = (lo + hi) // 2
        if len(greedy(words, mid)) <= len(best) and all(width(l) <= mid for l in greedy(words, mid)):
            hi = mid
        else:
            lo = mid + 1
    trial = greedy(words, lo)
    return trial if len(trial) == len(best) else best


def wrap(en, mid):
    """Return (wrapped text with {n}, errors). Pages split at {clr}/{wait}; {n} forces a break."""
    maxw, maxl = BOXES[form(mid)]
    if maxw is None:
        return en, []
    errors, out = [], []
    for page in re.split(r"(\{clr\}|\{wait\})", en):
        if page in ("{clr}", "{wait}") or not page:
            out.append(page)
            continue
        lines = []
        for para in page.split("{n}"):
            lines += wrap_para(para, maxw)
        for l in lines:
            if width(l) > maxw:
                errors.append(f"{mid}: line {width(l)}px > {maxw}px: {l!r}")
        if len(lines) > maxl:
            errors.append(f"{mid}: {len(lines)} lines > {maxl} ({form(mid)} box)")
        out.append("{n}".join(lines))
    return "".join(out), errors


if __name__ == "__main__":
    mid, s = sys.argv[1], sys.argv[2]
    text, errs = wrap(s, mid)
    print(f"form {form(mid)} {BOXES[form(mid)]}")
    for page in re.split(r"\{clr\}|\{wait\}", text):
        if page:
            for l in page.split("{n}"):
                print(f"{width(l):4d}px | {l}")
            print("----")
    print("\n".join(errs) or "OK")
