"""Tests for the ILP-DS schema, code lists, examples and tools."""
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
from check_ilp import check_document  # noqa: E402
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


def test_asset_classes_are_grouped_and_mapped():
    with (ROOT / "codelists" / "asset-class.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    groups = {row["value"]: row["group"] for row in rows}
    assert {v for v, g in groups.items() if g == "real-estate"} == {
        "commercial", "international-education-and-learning", "experience-economy",
        "frontier-innovation", "living", "logistics-and-light-industrial"}
    assert {v for v, g in groups.items() if g == "infrastructure"} == {
        "data-centres", "energy-and-decarbonisation", "transport"}
    assert groups["other"] == ""
    assert all(row["gresb"] for row in rows)


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
    published = load(ROOT / "schema" / "ilp-ds.context.jsonld")["@context"]
    inline = dict(doc["@context"])
    assert inline.pop("@base") == doc["base"]
    assert inline == published


# Failures the checker must catch

def test_unknown_code_is_rejected(doc):
    record(doc, "#example-site")["land-type"] = "greybelt"
    assert any("land-type" in p for p in check_document(doc))


def test_unknown_asset_class_is_rejected(doc):
    record(doc, "#example-site")["asset-classes"] = ["hotel"]
    assert any("asset-classes" in p for p in check_document(doc))


def test_repeated_asset_class_is_rejected(doc):
    record(doc, "#example-site")["asset-classes"] = ["living", "living"]
    assert any("asset-classes" in p for p in check_document(doc))


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
    assert "https://example.org/ilp-ds/locations#example-site" in ids
    site = next(n for n in nodes if n["@id"].endswith("#example-site"))
    ns = build_schema.NAMESPACE
    assert site[ns + "landType"][0]["@value"] == "brownfield"
    assert site[ns + "parent"][0]["@id"] == "https://example.org/ilp-ds/locations#example-cluster"


# 0.3: infrastructure, mineral extraction sites, jobs, status and stage

def test_infrastructure_with_line_and_serves_passes(doc):
    line = next(f for f in doc["features"] if f["id"] == "#example-link-line")
    assert line["geometry"]["type"] == "LineString"
    assert check_document(doc) == []


def test_line_shape_only_for_infrastructure(doc):
    site = next(f for f in doc["features"] if f["id"] == "#example-site")
    site["geometry"] = {"type": "LineString", "coordinates": [[-0.3, 51.5], [-0.29, 51.51]]}
    assert any("only infrastructure" in p for p in check_document(doc))


def test_serves_must_name_records_in_the_file(doc):
    record(doc, "#example-link-line")["serves"] = ["#nowhere"]
    assert any("not in this file" in p for p in check_document(doc))


def test_serves_only_on_infrastructure(doc):
    record(doc, "#example-site")["serves"] = ["#example-area"]
    assert check_document(doc)


def test_mineral_extraction_is_a_valid_kind(doc):
    doc["features"].append({"type": "Feature", "id": "#example-quarry", "geometry": None, "properties": {
        "kind": "mineral-extraction", "parent": "#example-area", "name": "Example Quarry (fictional)",
        "local-authorities": ["E09000017"], "land-type": "greenfield", "overall-status": "in-progress",
        "delivery-stage": "committee", "entry-date": "2026-10-18", "source": "Fictional example"}})
    assert check_document(doc) == []


def test_jobs_range(doc):
    area = record(doc, "#example-area")
    assert (area["jobs-from"], area["jobs-to"]) == (14000, 25000)
    area["jobs-to"] = 1000
    assert any("below jobs-from" in p for p in check_document(doc))


def test_jobs_to_needs_jobs_from(doc):
    site = record(doc, "#example-site")
    del site["jobs-from"]
    site["jobs-to"] = 2000
    assert any("jobs-from" in p for p in check_document(doc))


def test_old_combined_status_values_are_rejected(doc):
    record(doc, "#example-site")["overall-status"] = "in-progress-master-planning"
    assert any("overall-status" in p for p in check_document(doc))


def test_complete_has_no_delivery_stage(doc):
    site = record(doc, "#example-site")
    site["overall-status"] = "complete"
    assert any("no delivery-stage" in p for p in check_document(doc))


def test_gva_method_can_be_not_stated(doc):
    record(doc, "#example-site")["gva-method"] = "not-stated"
    assert check_document(doc) == []


def test_wla_priority_sectors_are_in_the_economic_driver_list():
    with (ROOT / "codelists" / "economic-driver.csv").open(newline="", encoding="utf-8") as handle:
        values = {row["value"] for row in csv.DictReader(handle)}
    assert {"createch", "frontier-innovation", "advanced-manufacturing", "clean-energy", "digital",
            "heathrow-linked-industries"} <= values


# 0.4: mineral extraction, investment required, named contacts

def test_old_mineral_extraction_site_kind_is_rejected(doc):
    record(doc, "#example-site")["kind"] = "mineral-extraction-site"
    assert any("kind" in p for p in check_document(doc))


def test_investment_required_is_a_value_type(doc):
    site = record(doc, "#example-site")
    site.update({"investment-value": 925000000, "value-type": "investment-required",
                 "value-source": "Fictional prospectus, p1 ('c.£925m')", "value-date": "2026-07-01"})
    assert check_document(doc) == []


def test_a_named_contact_is_published(doc):
    site = record(doc, "#example-site")
    site["contacts"] = [{"name": "Alex Example (fictional)", "role": "Head of Regeneration",
                         "email": "alex.example@example.org"}]
    assert check_document(doc) == []
    public = make_public(doc)[0]
    assert check_document(public) == []
    assert record(public, "#example-site")["contacts"][0]["name"] == "Alex Example (fictional)"


# 0.5: homes on areas, floorspace ranges, masterplan adopted, opportunity types

def test_opportunity_area_can_hold_pipeline_homes_and_floorspace(doc):
    area = record(doc, "#example-area")
    assert area["homes-pipeline"] == 12000
    assert area["floorspace-pipeline-to"]["total"] == 45000
    assert check_document(doc) == []


def test_floorspace_range_upper_not_below_lower(doc):
    record(doc, "#example-area")["floorspace-pipeline-to"] = {"total": 1000}
    assert any("is below floorspace-pipeline" in p for p in check_document(doc))


def test_floorspace_range_keys_must_match(doc):
    record(doc, "#example-area")["floorspace-pipeline-to"] = {"E(g)(i)": 50000}
    assert any("floorspace-pipeline does not" in p for p in check_document(doc))


def test_floorspace_range_needs_lower_figure(doc):
    area = record(doc, "#example-area")
    del area["floorspace-pipeline"]
    assert any("floorspace-pipeline" in p for p in check_document(doc))


def test_masterplan_adopted_is_a_stage(doc):
    assert record(doc, "#example-cluster")["delivery-stage"] == "masterplan-adopted"
    assert check_document(doc) == []


def test_other_opportunity_type_needs_notes(doc):
    site = record(doc, "#example-site")
    assert "other" in site["opportunity-types"]
    del site["opportunity-type-notes"]
    assert any("opportunity-type-notes" in p for p in check_document(doc))


def test_unknown_opportunity_type_is_rejected(doc):
    record(doc, "#example-site")["opportunity-types"] = ["handshake"]
    assert check_document(doc)



# 0.6: qualifiers for approximate and open-ended figures

def test_qualifiers_pass(doc):
    assert record(doc, "#example-area")["qualifiers"] == {"homes-pipeline": "at-least", "jobs-to": "up-to"}
    assert check_document(doc) == []


def test_qualifier_needs_its_figure(doc):
    record(doc, "#example-area")["qualifiers"]["gva-uplift"] = "about"
    assert any("qualifiers names gva-uplift" in p for p in check_document(doc))


def test_unknown_qualifier_is_rejected(doc):
    record(doc, "#example-area")["qualifiers"]["homes-pipeline"] = "roughly"
    assert check_document(doc)


def test_only_figures_can_be_qualified(doc):
    record(doc, "#example-area")["qualifiers"]["name"] = "about"
    assert check_document(doc)


def test_every_qualifiable_field_is_a_figure():
    figures = {f["field"] for f in build_schema.fields() if f["type"] in ("integer", "number", "floorspace")}
    assert set(build_schema.QUALIFIABLE) <= figures


# 0.7: completed homes

def test_homes_completed_within_consent(doc):
    site = record(doc, "#example-site")
    assert site["homes-completed"] <= site["homes-consented"]
    site["qualifiers"] = {"homes-completed": "about"}
    assert check_document(doc) == []


def test_homes_completed_above_consent_is_rejected(doc):
    site = record(doc, "#example-site")
    site["homes-completed"] = site["homes-consented"] + 1
    assert any("above homes-consented" in p for p in check_document(doc))


def test_area_can_hold_completed_homes(doc):
    record(doc, "#example-area")["homes-completed"] = 14500
    assert check_document(doc) == []


def codes(name):
    with open(ROOT / "codelists" / f"{name}.csv", newline="", encoding="utf-8") as f:
        return [row["value"] for row in csv.DictReader(f)]


def test_hybrid_permission_and_consented_stage(doc):
    site = record(doc, "#example-site")
    site["permission-type"] = "hybrid planning permission"
    site["delivery-stage"] = "consented"
    assert check_document(doc) == []
    assert "hybrid planning permission" in codes("permission-type")
    stages = codes("delivery-stage")
    assert stages.index("committee") < stages.index("consented") < stages.index("construction")


def test_consented_stage_needs_permission(doc):
    site = record(doc, "#example-site")
    site["delivery-stage"] = "consented"
    site["planning-status"] = "pending decision"
    assert any("consented needs planning-status permissioned" in p for p in check_document(doc))
