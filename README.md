# Report Synthesis

Decodes a Texas police crash report (form CR-3) into a plain-English brief for a
personal injury firm's first-week case check: what builds the case, what could
sink it, and which evidence deadlines are running.

## Status

Built:

- **Official code tables.** All 46 code sheets (558 codes) for the 2023 CR-3, built
  directly from TxDOT's CR-100 manual, version 29.0.
- **Decoder.** Turns every coded field into `code = meaning`. A code that is not in
  the official table is reported, never guessed.
- **Flags.** Rules that sort facts into possible dealbreakers, case builders,
  deadlines and report errors. Every flag names the report field it came from.
- **Brief.** Markdown output for a paralegal, or JSON for another system.

Not built yet:

- **Reading the PDF.** The decoder takes a structured record (JSON). Extracting that
  record from a report PDF needs real sample reports to build and test against.
- **Older form versions** (2010, 2015, 2017, 2018). Code meanings differ between
  versions, so other versions are refused until their tables are loaded.
- **Outside lookups** (federal carrier records, recalls, property records).
- **Narrative against codes.** Conflicts between the officer's narrative and the coded
  boxes are not detected; the narrative is only scanned for keywords.
- **Damage area codes.** These are defined in TxDOT's CR-80 Vehicle Damage Guide,
  which is not loaded. Direction of force and severity are decoded.

The deadline rules and legal notes in `cr3/flags.py` are pointers for an attorney
to confirm. No lawyer has reviewed them.

## Run it

Python 3.10 or later, no dependencies.

```
python -m cr3 examples/commercial_rear_end.json --client-unit 3
python -m cr3 examples/commercial_rear_end.json --client-unit 3 --json
python -m unittest discover -s tests
```

`--client-unit` is the unit number of the firm's client. Fault, impairment and
insurance facts are sorted into dealbreakers or case builders depending on whose
unit they are recorded against. Without it they are listed as unsorted facts.

`examples/commercial_rear_end.json` is a fictional report; its brief is in
`examples/commercial_rear_end.brief.md`.

## Input

A JSON record that mirrors the form, with codes exactly as written on the report.
The example file shows every supported field. Top-level keys:

| Key | Contents |
|---|---|
| `form_version` | `"2023"` |
| `identifiers` | crash ID, case ID, header checkboxes, unit and person totals |
| `crash` | date, time, county, city, `road`, `intersecting_road` |
| `units[]` | vehicle, `driver_license`, `owner_lessee`, `fin_resp`, `damage_ratings`, `persons[]`, `cmv`, `factors` |
| `disposition[]` | where each injured person was taken |
| `charges[]` | charge and citation per person |
| `conditions` | weather, light, surface, traffic control and road codes |
| `narrative` | the officer's narrative text |
| `investigator` | name, agency, report date, investigation complete |

Contributing factors and vehicle defects are separate lists because they use
separate code tables: code 14 is "Disabled in Traffic Lane" as a factor and
"Automation Failure" as a defect.

## Rebuilding the code tables

```
pdftotext -layout cr100-v29.pdf cr100.txt
python tools/build_code_tables.py cr100.txt cr3/data/tx_cr3_2023_codes.json
```

The manual is at
https://www.txdot.gov/content/dam/docs/division/trf/crash-records/cr100-v29.pdf
