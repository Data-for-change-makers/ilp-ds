# Contributing to ILP-DS

Thank you for your interest. ILP-DS is an early draft, and the most useful contributions now
are examples of the data you hold or need, and the fields or code list values that are missing.

## How to take part

- **Ask a question or suggest a change:** [open an issue](../../issues). Say what you need the
  data for and, if you can, show an example.
- **Propose an edit:** open a pull request. To change a field or a code list, edit
  `schema/fields.csv` or the CSV in `codelists/`, run `python tools/build_schema.py`, and check
  that `python -m pytest` passes. Never edit the generated files (`schema/ilp-ds.schema.json`,
  `schema/ilp-ds.context.jsonld`, `docs/fields.md`) by hand.
- **Talk to us:** [get in touch](https://www.dataforchangemakers.org.uk/contact/) through Data for
  Change Makers.

## Guidelines for fields

- Reuse a field from a published standard, with its original name and meaning, before adding a
  new one.
- Give every new field a one-sentence definition, the kinds of record it applies to, and a
  visibility: public, restricted (published only with consent) or internal (never published).
- Prefer a code list to free text when values will be compared or filtered.
- Do not add fields that hold personal data. The one exception is `contacts`, which may name a
  person and is always published, so supply a person's details only with their agreement.

## How changes are decided

During the 0.x drafts, West London Business reviews and approves changes and records each one
in [CHANGELOG.md](CHANGELOG.md). There is no formal process yet: shared rules will be agreed
once a second organisation commits to publishing or using ILP-DS data.

## Licensing of contributions

By contributing, you agree that your contribution is licensed under this repository's licences:
CC BY 4.0 for the specification, registry, code lists and examples, and MIT-0 for code.

Please be considerate and constructive in all discussions.
