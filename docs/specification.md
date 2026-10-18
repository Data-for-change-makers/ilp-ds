# ILP-DS: Investment Location Profile-Data Standard

**Version 0.4-draft, 18 October 2026.** This is an early draft for discussion. Names, fields and
code lists may change in any 0.x release. Do not rely on it for production data yet.

Maintained by [West London Business](https://www.westlondon.com) as part of
[Data for Change Makers](https://www.dataforchangemakers.org.uk). To comment or take part, open
an issue in this repository or [get in touch](https://www.dataforchangemakers.org.uk/contact/).

## 1. Purpose

Investors, councils and developers describe the same places in different ways: an
opportunity area in a planning document, a site on a brownfield register, a scheme in a
developer's brochure, a building in a 3D model. ILP-DS is a common format for the facts an
investor needs about a location, across real estate, infrastructure and mineral extraction
sites, kept in one record that a map, a 3D model and an open data
feed can all read.

ILP-DS does not invent what already exists. It takes identifiers, planning fields and code
lists from published UK standards (section 9), and adds only the investment facts that none of
them covers, such as asset class, land type, overall status, economic drivers and funding
status.

The key words MUST, SHOULD and MAY are used as in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## 2. Records

A profile is made of records of six kinds. Places are linked to the level above by `parent`;
infrastructure is linked to the places it serves by `serves`:

| Kind | What it is | Parent |
| --- | --- | --- |
| `opportunity-area` | A large area designated or promoted for growth, such as a GLA Opportunity Area | none |
| `cluster` | Neighbouring sites promoted together as one opportunity | an opportunity area, or none |
| `site` | A single development site | a cluster or an opportunity area, or none |
| `mineral-extraction` | A site where minerals such as sand and gravel are or will be extracted | a cluster or an opportunity area, or none |
| `infrastructure` | A route or network, such as a railway line or heat network, that serves several places | an opportunity area, or none |
| `building` | An existing or proposed building, usually in a 3D model | a site, cluster, mineral extraction site or infrastructure (required) |

An infrastructure record usually crosses several areas, so instead of one parent it lists the
ids of the areas, clusters and sites it serves in `serves`. A proposed orbital railway, for
example, serves each opportunity area it would connect.

Each fact is held once, at the level it belongs to, and linked rather than copied. A change to a
site's planning status therefore reaches the map, the 3D model and the open feed without editing
any of them separately.

## 3. The file

An ILP-DS file is a [GeoJSON](https://datatracker.ietf.org/doc/html/rfc7946) FeatureCollection,
so any GIS or web map can open it. Each record is one Feature.

| Member | Required | Meaning |
| --- | --- | --- |
| `type` | yes | `FeatureCollection` |
| `standard` | yes | `{"name": "ILP-DS", "version": "0.4-draft"}` |
| `publisher` | yes | The organisation publishing the file |
| `licence` | yes | The data's licence, as an SPDX identifier or URL, such as `CC-BY-4.0` |
| `base` | yes | The base URI of the records (section 3.1) |
| `public` | no | `true` for a file meant for publication (section 5) |
| `changelog` | no | Dated notes of changes: `[{"date": "2026-10-18", "note": "..."}]` |
| `@context` | SHOULD | The JSON-LD context, so the file can also be read as linked data (section 3.2) |
| `features` | yes | The records |

Each Feature has `type` (`Feature`), `id`, `geometry` and `properties`. `geometry` is a Point,
Polygon or MultiPolygon in WGS84 longitude and latitude, or `null` where no boundary is known.
Infrastructure may also be a LineString or MultiLineString, such as the route of a railway;
other kinds may not.
`properties` holds the fields in [fields.md](fields.md).

### 3.1 Identifiers

A record's `id` is a fragment identifier: `#` followed by lowercase letters, digits and hyphens,
such as `#old-oak`. It MUST be unique in the file and SHOULD never change. A record's permanent
URI is the file's `base` followed by its `id`, such as `https://westlondon.com/discover/sites#old-oak`.
`parent` holds the parent's `id`.

Other identifiers are adopted rather than invented: ONS GSS codes for councils, Planning Data
organisation references for planning authorities, planning application references, OS TOIDs for
buildings and UPRNs for addresses.

### 3.2 Linked data

The file is also JSON-LD 1.1. Copy `schema/ilp-ds.context.jsonld` into the file's `@context`
and add `"@base"` with the same value as `base`. ILP-DS terms use the namespace
`https://dataforchangemakers.org.uk/ns/ilp-ds#` (prefix `ilp:`); `name`, `description`, the
dates, `source` and `licence` use schema.org and Dublin Core terms. The namespace address does
not resolve yet; the context is carried inline until it does.

## 4. Fields

[fields.md](fields.md) lists every field, which kinds of record it applies to, whether it is
required, who may see it, and where it comes from. In summary:

- **Every record** needs `kind`, `name`, `entry-date` (the date it was last checked) and `source`.
- **Every record except a building** needs `local-authorities`.
- **A building** needs `parent`.
- Paired fields travel together: `gva-uplift` needs `gva-method`, `gva-source` and `gva-date`;
  `investment-value` needs `value-type`, `value-source` and `value-date`; `jobs-to` needs
  `jobs-from`.
- `description` has at most 400 words.

### 4.1 Local authorities and planning authorities

`local-authorities` lists the ONS GSS code of each council the record lies in, such as
`E09000009` for Ealing. GSS codes cover every council in the UK (E06 to E10 in England, W06 in
Wales, S12 in Scotland and N09 in Northern Ireland), so the field works outside London. Codes
change when councils merge or are reorganised: record the code current at `entry-date`.

`planning-authority` is separate because it can differ from the council. In Old Oak and Park
Royal, for example, the Old Oak and Park Royal Development Corporation decides applications, not
the three boroughs. Use its Planning Data organisation reference: `development-corporation:Q20648596`.

### 4.2 Land type

`land-type` takes `brownfield`, `brownfield-greyfield`, `greenfield`, `mixed` or `unknown`.

- **Brownfield** follows the NPPF definition of previously developed land
  ([Annex B](https://www.gov.uk/guidance/national-planning-policy-framework-annex-b-glossary)),
  which includes large areas of hardstanding such as car parks.
- **Greenfield**, land not previously developed, is in general use but not defined there.
- **Greyfield** has no statutory definition. It describes underused commercial, retail or
  light-industrial land, such as retail and business parks. Since the NPPF counts such land as
  brownfield, ILP-DS records it as a kind of brownfield.
- **Mixed** covers clusters and areas that include both.

Grey belt is not a land type: it is a Green Belt category in the NPPF, so it is not a value here.

### 4.3 Asset classes

`asset-classes` lists the kinds of asset a location offers investors. A location can offer
several, so the field is a list. The values follow the asset classes used by Opportunity London,
in two groups, plus `other`:

| Group | Values |
| --- | --- |
| Real estate | `commercial`, `international-education-and-learning`, `experience-economy`, `frontier-innovation`, `living`, `logistics-and-light-industrial` |
| Infrastructure | `data-centres`, `energy-and-decarbonisation`, `transport` |

The code list maps each value to its nearest equivalent in GRESB's real estate property types
and infrastructure sectors (GRESB's infrastructure sectors follow EDHECinfra's TICCS), so that
the data can be compared with what investors report to GRESB.

Asset class is not the same as `economic-drivers`, which names the sectors expected to create
demand, or `floorspace-consented`, which uses planning use classes. Further classes, such as
hotels, healthcare, water and waste, and social infrastructure, may be added.

### 4.4 Economic drivers

`economic-drivers` names the sectors expected to create demand. The list starts from the West
London Alliance's six priority growth sectors: `createch` (screen, media and creative
technology), `frontier-innovation`, `advanced-manufacturing`, `clean-energy`, `digital` and
`heathrow-linked-industries`. Finer values, such as `creative-tech`, `immersive-media`, `design`
and `fashiontech`, sit under `createch` in the code list's group column.

Asset classes and economic drivers are kept as separate fields, because they answer different
questions: what an investor can buy, and where demand comes from. Both drive the return, so a
display MAY show them together under one heading, such as "Drivers".

### 4.5 Status and stage

`overall-status` says whether a development is moving: `stalled`, `in-progress` or `complete`.
`delivery-stage` says how far it has got, where that is known: `visioning`, `master-planning`,
`committee` or `construction`. Keeping them apart lets a record say "in progress" when that is
all a source states, and lets a site be stalled at a known stage.

A whole opportunity area usually has schemes at several stages at once, so it normally has an
`overall-status` and no `delivery-stage`; the stage belongs on its clusters and sites. A complete
development has no delivery stage.

### 4.6 Vision and consent

Consented figures (`homes-consented`, `floorspace-consented`) and the owner's further vision
(`homes-pipeline`, `floorspace-pipeline`) are kept apart. Displays MUST label pipeline figures
as a vision, not a consent.

Jobs are recorded as the source states them. A single figure goes in `jobs-from`; a range such
as "14,000 to 25,000 jobs" goes in `jobs-from` and `jobs-to`. This follows the brownfield land
data standard, which records dwellings as a range from and to, and keeps the figures usable for
sorting and totals.

### 4.7 Estimates

GVA estimates vary widely with the method used (gross or net additional, the period, the
allowance for displacement). A GVA figure MUST carry its method, source and date, and an
investment figure its type, source and date.

`value-type` says what an investment figure measures: `gdv` (the expected value of the
completed development), `investment-required` (what the source says is needed to deliver it)
or `invested-to-date`. An investment requirement is a cost, not a value, so it MUST NOT be
recorded as a GDV. Where the source qualifies a figure, such as "c.£7.5bn" or "£2bn+", the
value holds the number and `value-source` SHOULD quote the source's wording. Where a source gives a GVA figure without a
method, `gva-method` is `not-stated`, and displays MUST say so beside the figure.

### 4.8 Publishers' own fields

A publisher MAY add fields of its own, named with an `x-` prefix, such as `x-discover-colour`.
Checkers ignore them. Anything another publisher would also need should be proposed for the
standard instead.

## 5. Who sees what

Some fields are judgements or commercially sensitive. Every field has one of three visibilities:

| Visibility | Fields | Rule |
| --- | --- | --- |
| public | most fields | May be published |
| restricted | `owner-vision`, `policy-alignment-local`, `policy-alignment-regional`, `policy-alignment-national`, `funding-status` | Published only once the owner (or, for policy alignment, the planning authority) has seen it and agreed, recorded by listing the field in the record's `published-with-consent` |
| internal | `land-assembly` | Never published |

Policy alignment is an assessment, not a published fact, so each one records the policy cited,
who assessed it and when.

A publisher keeps one internal file and publishes a copy made by `tools/export_public.py`, which
removes internal fields and unconsented restricted fields and marks the copy `"public": true`.
`tools/check_ilp.py` rejects a public file that still carries them.

`contacts` is public. A contact MAY name a person, with their role and work email address, and
anything supplied in `contacts` is published. Supply a person's details only when they have
agreed to be listed.

## 6. Linking to 3D models

ILP-DS records and 3D models share identifiers, so a model never holds facts of its own:

- Each building in a glTF 2.0 model is a named node whose name is the record's `id` without the
  `#`, such as `example-works-block-a`.
- At export, a script copies fields such as `overall-status` and `planning-references` from the
  record into the node's metadata (`EXT_structural_metadata`), so a change of status means
  re-exporting the model, not remodelling it.
- `story-stops` names the cameras in the model that tell the location's story, in order.
- `model-tier` says how detailed each building's model is.

## 7. Checking a file

```sh
pip install -r requirements.txt
python tools/check_ilp.py my-locations.geojson
python tools/export_public.py my-locations.geojson my-locations-public.geojson
```

The checker validates the file against `schema/ilp-ds.schema.json` and then checks what a
schema cannot: unique ids, parents that exist and sit one level up, the 400-word limit, a
matching `@base`, and the visibility rules in section 5.

## 8. Versions and changes

ILP-DS follows [semantic versioning](https://semver.org) from 1.0. Until then, any 0.x release
may change anything, and each change is recorded in [CHANGELOG.md](../CHANGELOG.md).

West London Business approves changes for now. There is deliberately no steering group or formal
change process at this stage. Shared rules will be agreed when a second organisation commits to
publishing or relying on ILP-DS data.

## 9. Relationship to other standards

| Standard | What ILP-DS takes from it |
| --- | --- |
| [Planning Data platform](https://www.planning.data.gov.uk) (MHCLG) | Organisation references; `name`, `organisation`, `start-date`, `end-date`, `entry-date`, `source` |
| [Brownfield land data standard](https://www.gov.uk/government/publications/brownfield-land-registers-data-standard/publish-your-brownfield-land-data) | `hectares`, `ownership-status`, `planning-status`, `permission-type`, `permission-date` and their code lists; `point` (GeoX, GeoY); `planning-documents-url` (PlanningHistory) |
| [GLA Planning Information Data Standard](https://london.gov.uk/sites/default/files/updated_non_technical_planning_data_standard.pdf) | `planning-references`, `homes-consented`, `floorspace-consented` |
| [GLA Opportunity Areas](https://data.london.gov.uk/dataset/opportunity-areas-epr7z) | `opportunity-area` names |
| ONS GSS codes | `local-authorities` |
| West London Alliance, Opportunity West London investment prospectus 2026/27 | The six priority growth sectors in the `economic-driver` code list |
| Opportunity London asset classes | The `asset-class` code list |
| [GRESB asset classification](https://guides.gresb.com/completingassessments/2026-real-estate-assessment/info/asset-and-portfolio-classification) (real estate) and [infrastructure sectors](https://guides.gresb.com/completing-gresb-assessments/completing-the-assessment/supporting-information/asset-classification) | The GRESB equivalents in the `asset-class` code list |
| [OS Open Identifiers](https://www.ordnancesurvey.co.uk/products/open-mastermap-programme/open-id-policy) | `toid`, `uprns` |
| [GeoJSON](https://datatracker.ietf.org/doc/html/rfc7946) (RFC 7946) | The file format and geometry |
| glTF 2.0 (ISO/IEC 12113:2022) with `EXT_structural_metadata` | The link between records and 3D models (section 6) |
| [NPPF Annex B](https://www.gov.uk/guidance/national-planning-policy-framework-annex-b-glossary) | The definition of brownfield (previously developed land) |

Its file conventions follow those of other Data for Change Makers standards, such as the
[Courses and Occupations Open Data Standard](https://www.dataforchangemakers.org.uk/coods/)
(COODS): adopt published fields unrenamed, keep new
fields in a separate namespace, give records stable identifiers, link records rather than copy
them, state the version in the file, check files automatically, and keep assessments internal
until agreed.
