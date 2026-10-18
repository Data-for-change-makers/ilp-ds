"""Tests for the REILP-DS schema, code lists, examples and tools."""
from __future__ import annotations

import copy
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_schema  # noqa: E402
from check_reilp import check_document  # noqa: E402
from export_public import make_public  # noqa: E402

INTERNAL_EXAMPLE = ROOT / "examples" / "example-internal.geojson"
PUBLIC_EXAMPLE = ROOT / "examples" / "example-public.geojson"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def record(doc: dict, rid: str) -> dict:
    return next(f["properties"] for f in doc["features"] if f["id"] == rid)


@pytest.fixture
def doc() -> dict:
    return load(INTERNAL_EXAMPLE)


# Generated files and registry

def test_generated_files_are_up_to_date():
    assert build_schema.main(["--check"]) == 0


def test_every_code_list_named_in_the_registry_exists():
    for field in build_schema.fields():
        for prefix in ("code:", "codes:"):
            if field["type"].startswith(prefix):
                assert (ROOT / "codelists" / f"{field['type'][len(prefix):]}.csv").exists(), field["field"]


def test_code_lists_have_unique_values():
    for path in (ROOT / "codelists").glob("*.csv"):
        with path.open(newline="", encoding="utf-8") as handle:
            values = [row["value"] for row in csv.DictReader(handle)]
        assert len(values) == len(set(values)), path.name


def test_registry_visibility_and_origin_values():
    for field in build_schema.fields():
        assert field["visibility"] in {"public", "restricted", "internal"}, field["field"]
        assert field["origin"] in {"core", "adopted", "extension"}, field["field"]


# Examples

def test_internal_example_passes(doc):
    assert check_document(doc) == []


def test_public_example_passes_and_matches_export(doc):
    public = load(PUBLIC_EXAMPLE)
    assert check_document(public) == []
    assert make_public(doc)[0] == public


def test_example_context_matches_published_context(doc):
    published = load(ROOT / "schema" / "reilp-ds.context.jsonld")["@context"]
    inline = dict(doc["@context"])
    assert inline.pop("@base") == doc["base"]
    assert inline == published


# Failures the checker must catch

def test_unknown_code_is_rejected(doc):
    record(doc, "#example-site")["land-type"] = "greybelt"
    assert any("land-type" in p for p in check_document(doc))


def test_unknown_field_is_rejected(doc):
    record(doc, "#example-site")["boroughs"] = ["E09000009"]
    assert any("boroughs" in p for p in check_document(doc))


def test_publisher_fields_with_x_prefix_are_allowed(doc):
    record(doc, "#example-site")["x-discover-colour"] = "#ff5200"
    assert check_document(doc) == []


def test_missing_local_authorities_is_rejected(doc):
    del record(doc, "#example-site")["local-authorities"]
    assert any("local-authorities" in p for p in check_document(doc))


def test_bad_gss_code_is_rejected(doc):
    record(doc, "#example-site")["local-authorities"] = ["E01000001"]  # an LSOA code, not a council
    assert check_document(doc)


def test_building_needs_a_parent(doc):
    del record(doc, "#example-works-block-a")["parent"]
    assert any("parent" in p for p in check_document(doc))


def test_field_not_for_this_kind_is_rejected(doc):
    record(doc, "#example-works-block-a")["land-assembly"] = "assembled"
    assert check_document(doc)


def test_duplicate_id_is_rejected(doc):
    doc["features"][3]["id"] = "#example-site"
    assert any("more than once" in p for p in check_document(doc))


def test_missing_parent_is_rejected(doc):
    record(doc, "#example-site")["parent"] = "#nowhere"
    assert any("not in this file" in p for p in check_document(doc))


def test_wrong_parent_kind_is_rejected(doc):
    record(doc, "#example-cluster")["parent"] = "#example-site"
    assert any("cannot have a site" in p for p in check_document(doc))


def test_long_description_is_rejected(doc):
    record(doc, "#example-site")["description"] = "word " * 401
    assert any("401 words" in p for p in check_document(doc))


def test_gva_needs_method_source_and_date(doc):
    del record(doc, "#example-site")["gva-method"]
    assert any("gva-method" in p for p in check_document(doc))


def test_assessed_alignment_needs_policy_and_assessor(doc):
    del record(doc, "#example-site")["policy-alignment-local"]["assessed-by"]
    assert check_document(doc)


def test_mismatched_base_is_rejected(doc):
    doc["@context"]["@base"] = "https://example.org/elsewhere"
    assert any("@base" in p for p in check_document(doc))


def test_internal_field_in_public_file_is_rejected(doc):
    doc["public"] = True
    problems = check_document(doc)
    assert any("land-assembly is internal" in p for p in problems)


def test_restricted_field_needs_consent_in_public_file(doc):
    public = make_public(doc)[0]
    site = record(public, "#example-site")
    site["published-with-consent"] = ["funding-status"]
    assert any("owner-vision is restricted" in p for p in check_document(public))


def test_export_keeps_consented_restricted_fields(doc):
    site = record(make_public(doc)[0], "#example-site")
    assert site["funding-status"] == "partly-secured"
    assert site["owner-vision"] == "clear"
    assert "land-assembly" not in site
    assert "policy-alignment-local" not in site


def test_export_does_not_change_the_input(doc):
    before = copy.deepcopy(doc)
    make_public(doc)
    assert doc == before


# JSON-LD

def test_public_example_expands_as_json_ld():
    jsonld = pytest.importorskip("pyld.jsonld")
    # pyld resolves @base only when the document has a URL of its own, as a published file would.
    expanded = jsonld.expand(load(PUBLIC_EXAMPLE), {"base": "https://example.org/files/example-public.geojson"})
    nodes = expanded[0]["https://purl.org/geojson/vocab#features"]
    ids = {node["@id"] for node in nodes}
    assert "https://example.org/reilp-ds/locations#example-site" in ids
    site = next(n for n in nodes if n["@id"].endswith("#example-site"))
    ns = build_schema.NAMESPACE
    assert site[ns + "landType"][0]["@value"] == "brownfield"
    assert site[ns + "parent"][0]["@id"] == "https://example.org/reilp-ds/locations#example-cluster"
