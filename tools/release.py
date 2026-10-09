"""Release: check -> build -> checksum -> romdiff -> BPS (re-applied and verified) -> README -> zip in release/.

    python -X utf8 tools/release.py --version 1.0
Never publishes anything; release/ is local and gitignored.
"""
import hashlib
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build  # noqa: E402
import text  # noqa: E402

ROOT = text.ROOT
SKILL = Path("H:/translation/.claude/skills/translate-retro-game/scripts")
NAME = "YuYuHakusho2_KakutouNoShou_EN"


def run(*cmd):
    r = subprocess.run([sys.executable, "-X", "utf8", *map(str, cmd)], cwd=ROOT)
    if r.returncode:
        sys.exit(f"release: failed: {' '.join(map(str, cmd))}")


def hashes(data):
    return f"CRC32 {zlib.crc32(data):08X}, MD5 {hashlib.md5(data).hexdigest()}, SHA-1 {hashlib.sha1(data).hexdigest()}"


def main():
    version = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else "1.0"
    run(ROOT / "tools" / "check.py")
    out = ROOT / "release"
    out.mkdir(exist_ok=True)
    built = ROOT / "build" / "yyh2_en.sfc"
    build.build(built, "en")
    final = out / f"{NAME}.sfc"
    run(SKILL / "bps.py", "snes-checksum", built, "--out", final)
    allowed = [l.split()[0] for l in (ROOT / "tools" / "allowed_ranges.txt").read_text().splitlines()
               if l.strip() and not l.startswith("#")]
    run(SKILL / "romdiff.py", text.ROM, final, "7FDC-7FDF", *allowed)
    patch = out / f"{NAME}_v{version}.bps"
    run(SKILL / "bps.py", "make", text.ROM, final, patch)
    readme = (ROOT / "docs" / "README.release.txt").read_text(encoding="utf-8")
    readme = (readme.replace("{VERSION}", version).replace("{BASE}", hashes(text.ROM.read_bytes()))
              .replace("{PATCHED}", hashes(final.read_bytes())))
    (out / "README.txt").write_text(readme, encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(out / f"{NAME}_v{version}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(patch, patch.name)
        z.write(out / "README.txt", "README.txt")
    final.unlink()                          # no patched ROM left lying around in release/
    print(f"release: {out / f'{NAME}_v{version}.zip'}")


if __name__ == "__main__":
    main()
