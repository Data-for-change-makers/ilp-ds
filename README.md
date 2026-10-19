# ILP-DS

**Investment Location Profile-Data Standard.** An open format for the facts an
investor needs about a place to invest in, across real estate, infrastructure and mineral
extraction sites: opportunity areas, clusters, sites and buildings, their asset classes, planning status, land type, economic drivers
and funding, linked to maps and 3D models.

> **Status: 0.10-draft.** We are in the early stages of exploring this standard. Names, fields and
> code lists may change in any 0.x release, so do not use it for production data yet.

ILP-DS is an initiative of [West London Business](https://www.westlondon.com), part of
[Data for Change Makers](https://www.dataforchangemakers.org.uk). If you would like to know more,
or to get involved in developing it, please [open an issue](../../issues) or
[get in touch](https://www.dataforchangemakers.org.uk/contact/).

ILP-DS was first published as REILP-DS (Real Estate Investment Location Profile-Data Standard)
and renamed when its scope widened to infrastructure. Mineral extraction sites are also in scope.

## What it does

- **One record per place**: opportunity areas, clusters, sites and buildings, each linked to
  the level above, plus mineral extraction sites and infrastructure such as railway lines,
  linked to the places they serve. Each fact is held once.
- **Built on existing standards.** Identifiers, planning fields and code lists come from the
  Planning Data platform, the brownfield land data standard, the GLA's planning data standard,
  ONS and Ordnance Survey. ILP-DS adds only what none of them covers.
- **Readable everywhere.** A file is GeoJSON, so any web map or GIS can open it, and JSON-LD, so
  it can be read as linked data.
- **Safe to publish.** Judgements and commercially sensitive fields are marked restricted or
  internal, and a tool makes the public copy without them.
- **Linked to 3D models.** Buildings in a glTF model carry their record's id, so a change of
  status is a re-export, not a remodel.

## Under consideration

- **An `innovation` record type** for innovation districts, clusters and corridors, which are
  networks of places rather than one place with a boundary (such as WestTech London).
- **Electricity capacity fields**, in megawatts: the electricity contracted now, the capacity
  available now, and the additional capacity a scheme needs.

See [the specification, section 2](docs/specification.md#2-records). Comments are welcome.

## Contents

| Path | What it holds |
| --- | --- |
| [docs/specification.md](docs/specification.md) | The specification |
| [docs/fields.md](docs/fields.md) | Every field and code list (generated) |
| [schema/fields.csv](schema/fields.csv) | The field registry: the source of truth |
| [codelists/](codelists) | The code lists, one CSV each |
| [schema/ilp-ds.schema.json](schema/ilp-ds.schema.json) | JSON Schema 2020-12 (generated) |
| [schema/ilp-ds.context.jsonld](schema/ilp-ds.context.jsonld) | JSON-LD context (generated) |
| [examples/](examples) | A fictional example, internal and public versions |
| [tools/](tools) | Build, check and public-export scripts |
| [tests/](tests) | Tests, run on every change |

## Using it

You need Python 3.10 or later.

```sh
pip install -r requirements.txt
python tools/check_ilp.py examples/example-internal.geojson
python tools/export_public.py examples/example-internal.geojson my-public-copy.geojson
```

The first live feed is West London Business's, at
[westlondon.com/discover/data](https://westlondon.com/discover/data/), which also feeds the cards on
[Discover West London](https://westlondon.com/discover/).

To change a field or a code list, edit `schema/fields.csv` or the CSV in `codelists/`, then run
`python tools/build_schema.py` to regenerate the schema, the context and `docs/fields.md`, and
`python -m pytest` to check everything still agrees.

## Changes

West London Business approves changes during the 0.x drafts, and records each one in
[CHANGELOG.md](CHANGELOG.md). Shared rules for deciding changes will be agreed once a second
organisation commits to publishing or using ILP-DS data. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

- The specification, field registry, code lists, schema, context and examples are licensed under
  [Creative Commons Attribution 4.0 International](LICENSE) (CC BY 4.0). Please credit
  "ILP-DS, West London Business".
- The scripts in `tools/` and `tests/` are licensed under [MIT No Attribution](LICENSE-CODE)
  (MIT-0).

Data that publishers create using ILP-DS is theirs, under whatever licence they choose.
Fields adopted from other standards keep the definitions their publishers gave them.
