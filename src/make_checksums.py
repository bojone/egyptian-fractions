#!/usr/bin/env python3
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED = {"SHA256SUMS", "symdiff_exact", "two_tail", "fixed_server"}
rows = []
for path in ROOT.rglob("*"):
    if path.is_symlink() or not path.is_file():
        continue
    relative = path.relative_to(ROOT)
    if ".git" in relative.parts or "__pycache__" in relative.parts or "tmp" in relative.parts or relative.parts[:2] == ("results", "validation"):
        continue
    if path.name in EXCLUDED or path.suffix in {".pyc", ".tmp"}:
        continue
    rows.append((relative.as_posix(), sha256(path.read_bytes()).hexdigest()))
content = "".join(f"{digest}  {name}\n" for name, digest in sorted(rows))
(ROOT / "SHA256SUMS").write_text(content)
print(f"wrote {len(rows)} entries to SHA256SUMS")
