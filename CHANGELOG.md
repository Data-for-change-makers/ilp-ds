# Changelog

All notable changes to REILP-DS are recorded here. Dates are in ISO 8601 format.

## 0.1-draft — 18 October 2026

First public draft, for discussion.

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
