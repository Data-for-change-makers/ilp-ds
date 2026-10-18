"""Make the public copy of a ILP-DS file.

Usage:
    python tools/export_public.py INTERNAL_FILE PUBLIC_FILE

Removes every internal field, and every restricted field that the record does not list in
published-with-consent, then marks the copy "public": true and checks it. The internal file
is not changed.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_ilp import INTERNAL, RESTRICTED, check_document  # noqa: E402


def make_public(doc: dict) -> tuple[dict, list[str]]:
    """Return the public copy of a document and a list of what was removed."""
    out = copy.deepcopy(doc)
    out["public"] = True
    removed: list[str] = []
    for feature in out.get("features", []):
        props = feature.get("properties", {})
        consented = set(props.get("published-with-consent", []))
        for name in sorted(INTERNAL | (RESTRICTED - consented)):
            if name in props:
                del props[name]
                removed.append(f"{feature.get('id')}: {name}")
    return out, removed


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    source, target = Path(argv[0]), Path(argv[1])
    doc = json.loads(source.read_text(encoding="utf-8"))
    public, removed = make_public(doc)
    problems = check_document(public)
    if problems:
        print("The public copy does not pass the check, so it was not written:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    target.write_text(json.dumps(public, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {target} ({len(removed)} fields removed)")
    for item in removed:
        print(f"  removed {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
