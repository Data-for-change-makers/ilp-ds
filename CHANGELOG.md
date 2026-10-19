# Changelog

All notable changes to ILP-DS are recorded here. Dates are in ISO 8601 format.

## 0.10-draft — 19 October 2026

- Displays SHOULD (was MUST) say when a GVA figure's method is not stated; the data still records
  `not-stated`.
- The specification and README note two ideas under consideration: an `innovation` record type
  for innovation districts, clusters and corridors, and electricity capacity fields in megawatts
  (contracted now, available now, additional required).
- The README links the first live feed, West London Business's.

## 0.9-draft — 19 October 2026

- `permission-type` is now a list, each type once, because a large site often holds several
  consents at once (for example a hybrid permission, reserved matters approvals under it and a
  later outline permission). A single value must now be written as a one-item list. The
  brownfield land data standard holds one value per site; ILP-DS allows more.
- The checker rejects a record that lists permission types but gives a `planning-status` other
  than `permissioned`.
- The example site now holds outline permission and reserved matters approval.

## 0.8-draft — 19 October 2026

- `permission-type` gains `hybrid planning permission`, for one decision that grants full
  permission for part of a development and outline permission for the rest. The value is added by
  ILP-DS; the rest of the list is the brownfield land data standard's.
- `delivery-stage` gains `consented`, between `committee` and `construction`: permission is granted
  and construction has not started. `committee` now also covers a resolution to grant whose
  decision has not yet been issued.
- The checker rejects a record at the `consented` stage whose `planning-status` is not
  `permissioned`.
- The example site's stage is corrected to `construction`, as it has completed homes.

## 0.7-draft — 19 October 2026

- New field `homes-completed`: homes built so far, part of `homes-consented` rather than in
  addition to it (specification 4.6). It may carry a qualifier, and opportunity areas may hold it.
- The checker rejects completed homes above consented ones.

## 0.6-draft — 19 October 2026

- New field `qualifiers`, with the code list `qualifier` (`about`, `at-least`, `up-to`), so
  figures such as "c.£7.5bn", "3,000+ homes" or "up to 14,000 homes" keep their meaning. It maps
  the field holding a figure to its qualifier (specification 4.8).
- Displays must show a qualifier with its figure, and show totals that include one as approximate.

## 0.5-draft — 19 October 2026

- Opportunity areas may hold `homes-pipeline` and `floorspace-pipeline`, such as a plan's capacity
  for the whole area.
- Pipeline figures are defined as beyond the consent, so consented plus pipeline is the total and
  never double counts (specification 4.6).
- New field `floorspace-pipeline-to` for the upper figures of a floorspace range.
- `delivery-stage` gains `masterplan-adopted`, for a masterplan adopted or approved before any
  planning application.
- New fields `opportunity-types` (joint venture, development partnership, capital investment,
  forward funding, land sale, occupier, other) and `opportunity-type-notes` for free text.
- GVA uplift with no stated period is recorded as yearly.
- The specification notes that innovation corridors made up of several clusters and districts
  have no record type yet, and could be a future one with sub-types.

## 0.4-draft — 18 October 2026

- Scope: mineral extraction sites are in scope alongside real estate and infrastructure.
- The kind `mineral-extraction-site` is renamed `mineral-extraction`.
- `value-type` gains `investment-required`, for the investment a source says is needed. It is
  not a gross development value.
- `contacts` may name a person with their work email address. Anything supplied in `contacts`
  is published.

## 0.3-draft — 18 October 2026

Changes found while preparing the first West London data from the West London Alliance's
Opportunity West London investment prospectus 2026/27.

- New kinds `infrastructure` (routes and networks, which may have a LineString or
  MultiLineString shape and list the places they connect in the new `serves` field) and
  `mineral-extraction-site`.
- `overall-status` is now `stalled`, `in-progress` or `complete`, and a new `delivery-stage`
  field holds `visioning`, `master-planning`, `committee` or `construction`. The combined values
  such as `in-progress-master-planning` are withdrawn.
- New fields `jobs-from` and `jobs-to`, so a range of jobs can be recorded.
- `gva-method` gains `not-stated`, for figures whose source gives no method.
- The `economic-driver` code list now starts from WLA's six priority growth sectors, with the
  earlier values grouped under `createch`.

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
