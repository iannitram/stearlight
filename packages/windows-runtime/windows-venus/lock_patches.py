"""List the Venus renderer patches named in sources.lock.json, in lock order."""

import hashlib
import json
import sys
from pathlib import Path


def verified_patches(root) -> list[Path]:
    root = Path(root)
    lock = json.loads((root / "sources.lock.json").read_text())
    entries = lock["patches"]
    listed = [root / entry["file"] for entry in entries]
    for entry, path in zip(entries, listed):
        if not path.is_file():
            raise ValueError(f"missing patch: {entry['file']}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"hash mismatch: {entry['file']}")
    names = {path.name for path in listed}
    for path in sorted((root / "patches").iterdir(), key=lambda p: p.name):
        if path.name.endswith(".patch") and path.name not in names:
            raise ValueError(f"unlisted patch: patches/{path.name}")
    return listed


def main(argv: list[str]) -> int:
    try:
        patches = verified_patches(argv[0])
    except ValueError as error:
        print(f"lock_patches: {error}", file=sys.stderr)
        return 1
    for path in patches:
        print(path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
