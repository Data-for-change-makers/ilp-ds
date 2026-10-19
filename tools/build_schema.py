"""Build the ILP-DS JSON Schema and JSON-LD context from the field registry.

schema/fields.csv and the files in codelists/ are the source of truth. This script writes
schema/ilp-ds.schema.json, schema/ilp-ds.context.jsonld and docs/fields.md from them. Do not
edit those three files by hand: change the registry or a code list, then run

    python tools/build_schema.py

The tests fail if the generated files are out of date.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.7-draft"
NAMESPACE = "https://dataforchangemakers.org.uk/ns/ilp-ds#"
SCHEMA_ID = "https://raw.githubusercontent.com/Data-for-change-makers/ilp-ds/main/schema/ilp-ds.schema.json"
# The figures a qualifier (about, at-least, up-to) may apply to.
QUALIFIABLE = ["hectares", "homes-consented", "homes-completed", "homes-pipeline", "floorspace-consented", "floorspace-pipeline",
               "floorspace-pipeline-to", "jobs-from", "jobs-to", "gva-uplift", "investment-value"]
KINDS = ["opportunity-area", "cluster", "site", "mineral-extraction", "infrastructure", "building"]

ID_PATTERN = r"^#[a-z0-9]+(-[a-z0-9]+)*$"
DATE = {"type": "string", "format": "date", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
URI = {"type": "string", "format": "uri", "pattern": r"^https?://"}
TEXT = {"type": "string", "minLength": 1}
FLOORSPACE = {
    "type": "object",
    "minProperties": 1,
    "description": "Square metres by use class, such as {\"E(g)(i)\": 12000, \"C3\": 30000}. A \"total\" key is allowed.",
    "additionalProperties": {"type": "number", "minimum": 0},
}

# Terms reused from established vocabularies; every other field gets a ilp: IRI.
REUSED_TERMS = {
    "name": "schema:name",
    "description": "schema:description",
    "start-date": "schema:startDate",
    "end-date": "schema:endDate",
    "entry-date": "dct:modified",
    "source": "dct:source",
    "licence": "dct:license",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def codelist(name: str) -> list[str]:
    return [row["value"] for row in read_csv(ROOT / "codelists" / f"{name}.csv")]


def fields() -> list[dict[str, str]]:
    return read_csv(ROOT / "schema" / "fields.csv")


def applies_to(field: dict[str, str]) -> list[str]:
    return KINDS if field["applies-to"] == "all" else field["applies-to"].split()


def field_schema(field: dict[str, str], restricted: list[str]) -> dict:
    kind = field["type"]
    if kind.startswith("code:"):
        schema = {"type": "string", "enum": codelist(kind[5:])}
    elif kind.startswith("codes:"):
        schema = {"type": "array", "minItems": 1, "uniqueItems": True,
                  "items": {"type": "string", "enum": codelist(kind[6:])}}
    elif kind == "string":
        schema = dict(TEXT)
        if field["field"] == "description":
            schema["maxLength"] = 4000  # the 400-word limit itself is checked by tools/check_ilp.py
    elif kind == "id":
        schema = {"type": "string", "pattern": ID_PATTERN}
    elif kind == "ids":
        schema = {"type": "array", "minItems": 1, "uniqueItems": True,
                  "items": {"type": "string", "pattern": ID_PATTERN}}
    elif kind == "integer":
        schema = {"type": "integer", "minimum": 0}
    elif kind == "number":
        schema = {"type": "number", "minimum": 0}
    elif kind == "boolean":
        schema = {"type": "boolean"}
    elif kind == "date":
        schema = dict(DATE)
    elif kind == "uri":
        schema = dict(URI)
    elif kind == "strings":
        schema = {"type": "array", "minItems": 1, "uniqueItems": True, "items": dict(TEXT)}
    elif kind == "gss-codes":
        schema = {"type": "array", "minItems": 1, "uniqueItems": True,
                  "items": {"type": "string", "pattern": r"^(E0[6-9]|E10|W06|S12|N09)\d{6}$"}}
    elif kind == "organisation-reference":
        schema = {"type": "string", "pattern": r"^[a-z][a-z-]*:[A-Za-z0-9-]+$"}
    elif kind == "lon-lat":
        schema = {"type": "array", "minItems": 2, "maxItems": 2, "prefixItems": [
            {"type": "number", "minimum": -180, "maximum": 180},
            {"type": "number", "minimum": -90, "maximum": 90}]}
    elif kind == "floorspace":
        schema = json.loads(json.dumps(FLOORSPACE))
    elif kind == "toid":
        schema = {"type": "string", "pattern": r"^osgb\d{13,16}$"}
    elif kind == "uprns":
        schema = {"type": "array", "minItems": 1, "uniqueItems": True,
                  "items": {"type": "string", "pattern": r"^\d{1,12}$"}}
    elif kind == "alignment":
        schema = {
            "type": "object",
            "required": ["alignment"],
            "additionalProperties": False,
            "properties": {
                "alignment": {"type": "string", "enum": codelist("policy-alignment")},
                "policy": dict(TEXT),
                "assessed-by": dict(TEXT),
                "assessed-date": dict(DATE),
            },
            "if": {"properties": {"alignment": {"not": {"const": "not-assessed"}}}},
            "then": {"required": ["policy", "assessed-by", "assessed-date"]},
        }
    elif kind == "contacts":
        schema = {"type": "array", "minItems": 1, "items": {
            "type": "object",
            "additionalProperties": False,
            "anyOf": [{"required": ["email"]}, {"required": ["url"]}],
            "properties": {"name": dict(TEXT), "role": dict(TEXT),
                           "email": {"type": "string", "format": "email", "pattern": "^[^@\\s]+@[^@\\s]+$"},
                           "url": dict(URI)}}}
    elif kind == "organisations":
        schema = {"type": "array", "minItems": 1, "items": {
            "type": "object", "required": ["name"], "additionalProperties": False,
            "properties": {"name": dict(TEXT), "url": dict(URI), "logo-url": dict(URI)}}}
    elif kind == "qualifiers":
        schema = {"type": "object", "minProperties": 1,
                  "propertyNames": {"enum": QUALIFIABLE},
                  "additionalProperties": {"type": "string", "enum": codelist("qualifier")}}
    elif kind == "field-names":
        schema = {"type": "array", "minItems": 1, "uniqueItems": True,
                  "items": {"type": "string", "enum": restricted}}
    else:
        raise ValueError(f"unknown type {kind!r} for {field['field']}")
    schema["description"] = field["definition"]
    return schema


def build_schema() -> dict:
    registry = fields()
    restricted = [f["field"] for f in registry if f["visibility"] == "restricted"]
    props = {f["field"]: field_schema(f, restricted) for f in registry}

    conditions = [
        {"if": {"properties": {"kind": {"const": "building"}}},
         "then": {"required": ["parent"]},
         "else": {"required": ["local-authorities"]}},
    ]
    for kind in KINDS:
        not_allowed = [f["field"] for f in registry if kind not in applies_to(f)]
        if not_allowed:
            conditions.append({"if": {"properties": {"kind": {"const": kind}}},
                               "then": {"properties": {name: False for name in not_allowed}}})

    position = {"type": "array", "minItems": 2, "maxItems": 3, "items": {"type": "number"}}
    ring = {"type": "array", "minItems": 4, "items": {"$ref": "#/$defs/position"}}
    polygon = {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/ring"}}
    line = {"type": "array", "minItems": 2, "items": {"$ref": "#/$defs/position"}}

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": f"ILP-DS {VERSION}: Investment Location Profile-Data Standard",
        "description": "A GeoJSON FeatureCollection of location profiles. Generated by tools/build_schema.py from schema/fields.csv and codelists/; do not edit by hand.",
        "type": "object",
        "required": ["type", "standard", "publisher", "licence", "base", "features"],
        "properties": {
            "@context": {"description": "The JSON-LD context, normally schema/ilp-ds.context.jsonld inline, with @base set to the file's base.",
                         "type": ["object", "array", "string"]},
            "type": {"const": "FeatureCollection"},
            "standard": {"type": "object", "required": ["name", "version"], "additionalProperties": False,
                         "properties": {"name": {"const": "ILP-DS"}, "version": {"const": VERSION}}},
            "publisher": dict(TEXT, description="The organisation that publishes the file."),
            "licence": dict(TEXT, description="The licence for the file's data, as a URL or SPDX identifier, such as CC-BY-4.0."),
            "base": dict(URI, description="The base URI of the records. A record's permanent URI is the base followed by its id."),
            "public": {"type": "boolean", "description": "True for a file meant for publication. tools/check_ilp.py then rejects internal fields and unconsented restricted fields."},
            "changelog": {"type": "array", "items": {
                "type": "object", "required": ["date", "note"], "additionalProperties": False,
                "properties": {"date": dict(DATE), "note": dict(TEXT)}}},
            "features": {"type": "array", "items": {"$ref": "#/$defs/feature"}},
        },
        "additionalProperties": False,
        "$defs": {
            "position": position,
            "ring": ring,
            "feature": {
                "type": "object",
                "required": ["type", "id", "geometry", "properties"],
                "additionalProperties": False,
                "properties": {
                    "type": {"const": "Feature"},
                    "id": {"type": "string", "pattern": ID_PATTERN,
                           "description": "A fragment identifier, unique in the file, such as #old-oak."},
                    "geometry": {"oneOf": [
                        {"type": "null"},
                        {"type": "object", "required": ["type", "coordinates"], "additionalProperties": False,
                         "properties": {"type": {"const": "Point"}, "coordinates": {"$ref": "#/$defs/position"}}},
                        {"type": "object", "required": ["type", "coordinates"], "additionalProperties": False,
                         "properties": {"type": {"const": "Polygon"}, "coordinates": polygon}},
                        {"type": "object", "required": ["type", "coordinates"], "additionalProperties": False,
                         "properties": {"type": {"const": "MultiPolygon"},
                                        "coordinates": {"type": "array", "minItems": 1, "items": polygon}}},
                        {"type": "object", "required": ["type", "coordinates"], "additionalProperties": False,
                         "properties": {"type": {"const": "LineString"}, "coordinates": line}},
                        {"type": "object", "required": ["type", "coordinates"], "additionalProperties": False,
                         "properties": {"type": {"const": "MultiLineString"},
                                        "coordinates": {"type": "array", "minItems": 1, "items": line}}},
                    ]},
                    "properties": {"$ref": "#/$defs/properties"},
                },
            },
            "properties": {
                "type": "object",
                "required": ["kind", "name", "entry-date", "source"],
                "properties": props,
                "patternProperties": {"^x-": {"description": "A publisher's own field, outside the standard."}},
                "additionalProperties": False,
                "dependentRequired": {
                    "gva-uplift": ["gva-method", "gva-source", "gva-date"],
                    "investment-value": ["value-type", "value-source", "value-date"],
                    "jobs-to": ["jobs-from"],
                    "floorspace-pipeline-to": ["floorspace-pipeline"],
                },
                "allOf": conditions,
            },
        },
    }


def camel(name: str) -> str:
    head, *rest = name.split("-")
    return head + "".join(part.capitalize() for part in rest)


def build_context() -> dict:
    ctx: dict = {
        "@version": 1.1,
        "geojson": "https://purl.org/geojson/vocab#",
        "ilp": NAMESPACE,
        "schema": "https://schema.org/",
        "dct": "http://purl.org/dc/terms/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "type": "@type",
        "id": "@id",
        "FeatureCollection": "geojson:FeatureCollection",
        "Feature": "geojson:Feature",
        "Point": "geojson:Point",
        "Polygon": "geojson:Polygon",
        "MultiPolygon": "geojson:MultiPolygon",
        "LineString": "geojson:LineString",
        "MultiLineString": "geojson:MultiLineString",
        "features": {"@id": "geojson:features", "@container": "@set"},
        "geometry": "geojson:geometry",
        "coordinates": {"@id": "geojson:coordinates", "@container": "@list"},
        "properties": "@nest",
        "standard": {"@id": "dct:conformsTo", "@type": "@json"},
        "publisher": "dct:publisher",
        "public": None,
        "base": None,
        "changelog": None,
    }
    for f in fields():
        name, kind = f["field"], f["type"]
        iri = REUSED_TERMS.get(name, f"ilp:{camel(name)}")
        if kind in ("date",):
            ctx[name] = {"@id": iri, "@type": "xsd:date"}
        elif kind in ("integer",):
            ctx[name] = {"@id": iri, "@type": "xsd:integer"}
        elif kind in ("number",):
            ctx[name] = {"@id": iri, "@type": "xsd:decimal"}
        elif kind in ("boolean",):
            ctx[name] = {"@id": iri, "@type": "xsd:boolean"}
        elif kind in ("id",):
            ctx[name] = {"@id": iri, "@type": "@id"}
        elif kind in ("ids",):
            ctx[name] = {"@id": iri, "@type": "@id", "@container": "@set"}
        elif kind in ("uri",):
            ctx[name] = {"@id": iri, "@type": "@id"}
        elif kind in ("lon-lat",):
            ctx[name] = {"@id": iri, "@container": "@list"}
        elif kind in ("floorspace", "alignment", "contacts", "organisations", "qualifiers"):
            ctx[name] = {"@id": iri, "@type": "@json"}
        elif kind.startswith("codes:") or kind in ("strings", "gss-codes", "uprns", "field-names"):
            ctx[name] = {"@id": iri, "@container": "@set"}
        else:
            ctx[name] = iri
    return {"@context": ctx}


def build_field_docs() -> str:
    """Write the field and code list reference as Markdown."""
    origins = [
        ("core", "Structure", "Fields that hold the records together."),
        ("adopted", "Fields adopted from published standards",
         "These keep the name and meaning they have in the standard they come from."),
        ("extension", "ILP-DS extension fields",
         "Fields no published standard covers, defined by ILP-DS in its own namespace."),
    ]
    lines = [
        "# ILP-DS fields and code lists",
        "",
        f"Version {VERSION}. Generated by `tools/build_schema.py` from `schema/fields.csv` and `codelists/`;",
        "do not edit this page by hand.",
        "",
        "Required: **yes** for every record; **building** or **not building** where it depends on the kind.",
        "Visibility: **public**; **restricted** (published only once listed in `published-with-consent`);",
        "**internal** (never published). See the [specification](specification.md#who-sees-what).",
        "",
    ]
    registry = fields()
    for origin, title, intro in origins:
        lines += [f"## {title}", "", intro, "",
                  "| Field | Applies to | Type | Required | Visibility | Source | Definition |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for f in registry:
            if f["origin"] != origin:
                continue
            kinds = "all" if f["applies-to"] == "all" else ", ".join(f["applies-to"].split())
            ftype = f["type"]
            if ftype.startswith(("code:", "codes:")):
                name = ftype.split(":", 1)[1]
                ftype = f"[{ftype}](#{name})"
            lines.append(f"| `{f['field']}` | {kinds} | {ftype} | {f['required']} | {f['visibility']} | "
                         f"{f['source']} | {f['definition']} |")
        lines.append("")
    lines += ["## Code lists", ""]
    for path in sorted((ROOT / "codelists").glob("*.csv")):
        rows = read_csv(path)
        extra = [c for c in rows[0] if c not in ("value", "label", "definition", "source")]
        headings = {"group": "Group", "gresb": "GRESB equivalent"}
        sources = "; ".join(dict.fromkeys(r["source"] for r in rows))
        lines += [f"### {path.stem}", "", f"File: `codelists/{path.name}`. Source: {sources}.", "",
                  "| Value | Label | Definition |" + "".join(f" {headings.get(c, c)} |" for c in extra),
                  "| --- | --- | --- |" + " --- |" * len(extra)]
        lines += [f"| `{r['value']}` | {r['label']} | {r['definition']} |" + "".join(f" {r[c]} |" for c in extra)
                  for r in rows]
        lines.append("")
    return "\n".join(lines)


def dump(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    targets = {
        ROOT / "schema" / "ilp-ds.schema.json": dump(build_schema()),
        ROOT / "schema" / "ilp-ds.context.jsonld": dump(build_context()),
        ROOT / "docs" / "fields.md": build_field_docs(),
    }
    if "--check" in argv:
        stale = [p.name for p, text in targets.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print("Out of date: " + ", ".join(stale) + ". Run python tools/build_schema.py.")
            return 1
        print("Generated files are up to date.")
        return 0
    for path, text in targets.items():
        path.write_text(text, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
