#!/usr/bin/env python3
from fractions import Fraction
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUTPUT = []


def run(arguments, expected_code):
    process = subprocess.run(arguments, cwd=SRC, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    text = process.stdout
    if process.returncode != expected_code:
        raise AssertionError((arguments, process.returncode, text))
    return text


def negative(n, k, rmax):
    text = run([str(SRC / "symdiff_exact"), str(n), str(k), "1", str(rmax)], 1)
    if "result=yes" in text or "result=no" not in text:
        raise AssertionError((n, k, text))
    OUTPUT.append(f"PASS: no {k}-term representation of {n} (complete r=1..{rmax})")


def positive(n, k, rmax):
    text = run([str(SRC / "symdiff_exact"), str(n), str(k), "1", str(rmax)], 0)
    lines = [line for line in text.splitlines() if line.startswith(f"{n} {k} :")]
    if len(lines) != 1:
        raise AssertionError(text)
    values = list(map(int, lines[0].split(":", 1)[1].split()))
    if len(values) != len(set(values)) or sum((Fraction(1, a) for a in values), Fraction()) != n:
        raise AssertionError((n, k, values))
    OUTPUT.append(f"PASS: independently verified a {k}-term representation of {n}")


def main():
    if not (SRC / "symdiff_exact").exists():
        raise SystemExit("build first with: make cpu")
    negative(3, 11, 2)
    negative(3, 12, 3)
    positive(3, 13, 2)
    negative(4, 31, 5)
    negative(4, 32, 7)
    positive(4, 33, 3)
    negative(5, 83, 3)
    OUTPUT.append("SELFTEST_OK")
    destination = ROOT / "results" / "validation" / "selftest.log"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(OUTPUT) + "\n")
    print("\n".join(OUTPUT))


if __name__ == "__main__":
    main()
