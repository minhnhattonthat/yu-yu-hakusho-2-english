import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import text  # noqa: E402

ROM = text.ROM.read_bytes()


def test_roundtrip_every_string():
    for table, count in ((text.MSG_TABLE, text.MSG_COUNT), (text.SUB_TABLE, text.SUB_COUNT)):
        for i, off, jp, used in text.read_table(ROM, table, count):
            assert text.JP.encode(jp) == ROM[off:off + used], (hex(table), i)


def test_text_range_fully_covered():
    spans = []
    for table, count in ((text.MSG_TABLE, text.MSG_COUNT), (text.SUB_TABLE, text.SUB_COUNT)):
        spans += [(off, off + used) for _, off, _, used in text.read_table(ROM, table, count)]
    spans.append((text.SUB_TABLE, text.SUB_TABLE + 2 * text.SUB_COUNT))
    pos = text.TEXT_START
    for a, b in sorted(spans):
        assert a <= pos, f"uncovered bytes {pos:X}-{a:X}"
        pos = max(pos, b)
    assert pos == text.TEXT_END
