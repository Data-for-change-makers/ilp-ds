# Changelog

All notable changes to ILP-DS are recorded here. Dates are in ISO 8601 format.

## 0.2-draft — 18 October 2026

- Renamed from REILP-DS (Real Estate Investment Location Profile-Data Standard) to ILP-DS
  (Investment Location Profile-Data Standard), as the scope now covers infrastructure as well as
  real estate. The repository, file names, namespace (`https://dataforchangemakers.org.uk/ns/ilp-ds#`,
  prefix `ilp:`) and schema identifier changed with it.
- New field `asset-classes`, with a code list of Opportunity London's nine asset classes in two
  groups (real estate and infrastructure) plus `other`, each mapped to GRESB's property types
  and infrastructure sectors.

## 0.1-draft — 18 October 2026

First public draft, for discussion, published as REILP-DS.

- Four kinds of record (opportunity area, cluster, site, building), linked by `parent`.
- File format: a GeoJSON FeatureCollection that is also JSON-LD 1.1, with a `base` URI and
  fragment identifiers for records.
- 22 fields adopted from the Planning Data platform, the brownfield land data standard, the GLA
  Planning Information Data Standard, GLA Opportunity Areas, ONS GSS codes and OS Open
  Identifiers.
- 30 extension fields, including `land-type`, `overall-status`, `land-assembly`,
  `owner-vision`, policy alignment, `economic-drivers`, GVA, investment value and
  `funding-status`.
- Three visibilities (public, restricted, internal) and `published-with-consent`.
- 14 code lists, a field registry, a generated JSON Schema, JSON-LD context and field reference,
  a fictional example, a checker, a public-export tool and tests.
