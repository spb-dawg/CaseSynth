# CaseSynth

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

- **Outside lookups** (`--lookups`). For each vehicle, NHTSA's VIN decode, recalls and
  owner complaints; for each commercial vehicle with a USDOT number, the carrier's
  FMCSA record (status, authority, fleet size, inspections and out-of-service rates
  against the national average, reported crashes, safety rating, and with a key the
  liability insurance on file). Findings become flags: a recall on the same system as
  the officer's defect code, an above-average out-of-service rate, insurance on file
  below the required amount, a carrier name that does not match its USDOT number, a
  VIN that does not decode or does not match the vehicle on the report.

Not built yet:

- **Reading the PDF.** The decoder takes a structured record (JSON). Extracting that
  record from a report PDF needs real sample reports to build and test against.
- **Older form versions** (2010, 2015, 2017, 2018). Code meanings differ between
  versions, so other versions are refused until their tables are loaded.
- **More outside lookups.** Per-inspection violation detail, the carrier's insurer and
  policy (FMCSA's L&I system), Texas-only carriers (TxDMV numbers), property records.
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

```
python -m cr3 examples/commercial_rear_end.json --client-unit 3 --lookups
```

`--lookups` goes online. It sends only the VIN and USDOT number from the report to
NHTSA and FMCSA; no names, addresses, plates or policy numbers leave the machine.
A lookup that fails is flagged in the brief and does not stop it. Recalls and
complaints are for the make, model and year, so a specific VIN's recall status still
has to be confirmed.

The carrier record comes from FMCSA's QCMobile API when the `FMCSA_WEBKEY` environment
variable holds a WebKey (free, from https://mobile.fmcsa.dot.gov/QCDevsite/). The key
is sent only to `mobile.fmcsa.dot.gov` and never appears in the brief, the JSON or an
error message. Without a key, or if the API call fails for any reason, the record is
read from FMCSA's public SAFER snapshot page instead and the brief says so. The two
sources differ in small ways: the page gives a combined inspection total, the API gives
insurance on file and MC numbers from a second request.

```
FMCSA_WEBKEY=... python -m cr3 examples/commercial_rear_end.json --client-unit 3 --lookups
```

The example report uses made-up VINs and a made-up USDOT number, so a live run on it
reports that they do not check out. `examples/commercial_rear_end.lookups.brief.md`
shows the output with lookups, generated from saved responses: the carrier is
fictional, the Kenworth recalls and Camry complaints are real NHTSA records.

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
