"""Check ILP-DS files.

Usage:
    python tools/check_ilp.py FILE [FILE ...]

Each file is checked against the JSON Schema and then against the rules a schema cannot
express:

* every id is unique, and every parent names a record in the same file;
* a parent is one level up (a building's parent is a site or cluster, and so on);
* every id in serves names a record in the same file;
* only infrastructure has a line shape;
* jobs-to is not below jobs-from, and a complete development has no delivery stage;
* each floorspace-pipeline-to figure has a matching floorspace-pipeline figure and is not below it;
* opportunity-types including other comes with opportunity-type-notes;
* every figure named in qualifiers is in the record;
* homes-completed is not above homes-consented;
* a description has no more than 400 words;
* the JSON-LD @base, if given, matches the file's base;
* a file marked "public": true carries no internal fields, and carries a restricted field
  only where the record lists it in published-with-consent.

Exit status is 0 when every file passes and 1 otherwise.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "ilp-ds.schema.json").read_text(encoding="utf-8"))
with (ROOT / "schema" / "fields.csv").open(newline="", encoding="utf-8") as handle:
    REGISTRY = {row["field"]: row for row in csv.DictReader(handle)}

INTERNAL = {name for name, row in REGISTRY.items() if row["visibility"] == "internal"}
RESTRICTED = {name for name, row in REGISTRY.items() if row["visibility"] == "restricted"}
MAX_WORDS = 400

# The kinds a record of each kind may name as its parent.
PARENT_KINDS = {
    "opportunity-area": set(),
    "cluster": {"opportunity-area"},
    "site": {"opportunity-area", "cluster"},
    "mineral-extraction": {"opportunity-area", "cluster"},
    "infrastructure": {"opportunity-area"},
    "building": {"cluster", "site", "mineral-extraction", "infrastructure"},
}
LINES = {"LineString", "MultiLineString"}


def context_base(context) -> str | None:
    """Return the @base declared in an inline @context, if any."""
    items = context if isinstance(context, list) else [context]
    for item in items:
        if isinstance(item, dict):
            inner = item.get("@context", item)
            if isinstance(inner, dict) and "@base" in inner:
                return inner["@base"]
    return None


def check_document(doc: dict) -> list[str]:
    """Return a list of problems with one ILP-DS document (empty if it passes)."""
    problems: list[str] = []
    validator = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(part) for part in error.absolute_path) or "(file)"
        problems.append(f"{where}: {error.message}")
    if problems:
        return problems  # the rules below assume a well-formed file

    base = context_base(doc.get("@context"))
    if base is not None and base != doc["base"]:
        problems.append(f"(file): @base in @context is {base!r} but base is {doc['base']!r}")

    records = {}
    shapes = {}
    for feature in doc["features"]:
        if feature["id"] in records:
            problems.append(f"{feature['id']}: id is used more than once")
        records[feature["id"]] = feature["properties"]
        shapes[feature["id"]] = (feature["geometry"] or {}).get("type")

    public = doc.get("public", False)
    for rid, props in records.items():
        parent = props.get("parent")
        if parent is not None:
            if parent == rid:
                problems.append(f"{rid}: a record cannot be its own parent")
            elif parent not in records:
                problems.append(f"{rid}: parent {parent} is not in this file")
            elif records[parent]["kind"] not in PARENT_KINDS[props["kind"]]:
                problems.append(f"{rid}: a {props['kind']} cannot have a {records[parent]['kind']} as its parent")

        for served in props.get("serves", []):
            if served == rid:
                problems.append(f"{rid}: infrastructure cannot serve itself")
            elif served not in records:
                problems.append(f"{rid}: serves {served}, which is not in this file")

        if shapes[rid] in LINES and props["kind"] != "infrastructure":
            problems.append(f"{rid}: only infrastructure can have a {shapes[rid]} shape")

        if "jobs-to" in props and props["jobs-to"] < props.get("jobs-from", 0):
            problems.append(f"{rid}: jobs-to ({props['jobs-to']}) is below jobs-from ({props['jobs-from']})")

        low, high = props.get("floorspace-pipeline", {}), props.get("floorspace-pipeline-to", {})
        for key, value in high.items():
            if key not in low:
                problems.append(f"{rid}: floorspace-pipeline-to has {key} but floorspace-pipeline does not")
            elif value < low[key]:
                problems.append(f"{rid}: floorspace-pipeline-to {key} ({value}) is below floorspace-pipeline ({low[key]})")

        if props.get("homes-completed", 0) > props.get("homes-consented", float("inf")):
            problems.append(f"{rid}: homes-completed ({props['homes-completed']}) is above homes-consented ({props['homes-consented']})")

        for name in props.get("qualifiers", {}):
            if name not in props:
                problems.append(f"{rid}: qualifiers names {name}, which this record does not have")

        if "other" in props.get("opportunity-types", []) and not props.get("opportunity-type-notes"):
            problems.append(f"{rid}: opportunity-types includes other, so opportunity-type-notes must say what it is")

        if props.get("permission-type") and props.get("planning-status", "permissioned") != "permissioned":
            problems.append(f"{rid}: permission-type lists permissions granted, so planning-status must be permissioned, not {props['planning-status']}")

        if props.get("delivery-stage") == "consented" and props.get("planning-status", "permissioned") != "permissioned":
            problems.append(f"{rid}: delivery-stage consented needs planning-status permissioned, not {props['planning-status']}")

        if props.get("overall-status") == "complete" and "delivery-stage" in props:
            problems.append(f"{rid}: a complete development has no delivery-stage")

        words = len(props.get("description", "").split())
        if words > MAX_WORDS:
            problems.append(f"{rid}: description has {words} words; the limit is {MAX_WORDS}")

        if public:
            for name in sorted(INTERNAL & props.keys()):
                problems.append(f"{rid}: {name} is internal and must not be in a public file")
            consented = set(props.get("published-with-consent", []))
            for name in sorted((RESTRICTED & props.keys()) - consented):
                problems.append(f"{rid}: {name} is restricted; publish it only once it is listed in published-with-consent")
    return problems


def check_file(path: Path) -> list[str]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"(file): cannot read: {exc}"]
    if not isinstance(doc, dict):
        return ["(file): the top level must be a JSON object"]
    return check_document(doc)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    failed = False
    for name in argv:
        problems = check_file(Path(name))
        if problems:
            failed = True
            print(f"FAIL {name}")
            for problem in problems:
                print(f"  {problem}")
        else:
            print(f"PASS {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
