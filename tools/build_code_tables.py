"""Build cr3/data/tx_cr3_2023_codes.json from the official TxDOT CR-100 manual.

Usage:
    pdftotext -layout cr100-v29.pdf cr100.txt
    python tools/build_code_tables.py cr100.txt cr3/data/tx_cr3_2023_codes.json

Source: "CR-100 Instructions to Police for Reporting Crashes", version 29.0
https://www.txdot.gov/content/dam/docs/division/trf/crash-records/cr100-v29.pdf

Every value comes from the manual text. Nothing is filled in from memory. Entries
that wrap across lines in the PDF are fixed in PATCHES, each checked by hand
against the manual.
"""
import json
import re
import sys

# heading text in the manual -> (code sheet number, table key)
TABLES = [
    ("FOR ROADWAY SYSTEM", 1, "roadway_system"),
    ("FOR ROADWAY PART", 2, "roadway_part"),
    ("FOR STREET PREFIX", 3, "direction"),
    ("FOR DIRECTION", 3, "direction"),
    ("FOR STREET SUFFIX", 4, "street_suffix"),
    ("FOR UNIT DESCRIPTION", 5, "unit_description"),
    ("FOR VEHICLE COLOR", 6, "vehicle_color"),
    ("FOR BODY STYLE", 7, "body_style"),
    ("FOR AUTONOMOUS UNIT", 8, "autonomous_unit"),
    ("FOR AUTONOMOUS LEVEL", 9, "autonomous_level"),
    ("FOR DRIVER LICENSE/ID TYPE", 10, "dl_id_type"),
    ("FOR DRIVER LICENSE CLASS", 11, "dl_class"),
    ("FOR COMMERCIAL DRIVER LICENSE ENDORSEMENTS", 12, "cdl_endorsements"),
    ("FOR DRIVER LICENSE RESTRICTIONS", 13, "dl_restrictions"),
    ("FOR PERSON TYPE", 14, "person_type"),
    ("FOR SEAT POSITION", 15, "seat_position"),
    ("FOR INJURY SEVERITY", 16, "injury_severity"),
    ("FOR ETHNICITY", 17, "ethnicity"),
    ("FOR SEX", 18, "sex"),
    ("FOR EJECTED", 19, "ejected"),
    ("FOR RESTRAINT USED", 20, "restraint"),
    ("FOR AIRBAG", 21, "airbag"),
    ("FOR HELMET USE", 22, "helmet"),
    ("FOR SOLICITATION", 23, "solicitation"),
    ("FOR ALCOHOL SPECIMEN TYPE", 24, "alcohol_specimen"),
    ("FOR DRUG SPECIMEN TYPE", 25, "drug_specimen"),
    ("FOR DRUG TEST RESULTS", 26, "drug_result"),
    ("FOR DRUG CATEGORY", 27, "drug_category"),
    ("FOR FINANCIAL RESPONSIBILITY TYPE", 28, "fin_resp_type"),
    ("FOR VEHICLE DAMAGE RATING", 29, "damage_rating_special"),
    ("FOR VEHICLE OPERATION", 30, "vehicle_operation"),
    ("FOR CARRIER ID TYPE", 31, "carrier_id_type"),
    ("FOR VEHICLE TYPE", 32, "cmv_vehicle_type"),
    ("FOR BUS TYPE", 33, "bus_type"),
    ("FOR HAZARDOUS MATERIAL CLASS NUMBER", 34, "hazmat_class"),
    ("FOR CARGO BODY TYPE", 35, "cargo_body_type"),
    ("FOR TRAILER TYPE", 36, "trailer_type"),
    ("FOR SEQUENCE OF EVENTS", 37, "sequence_of_events"),
    ("FOR FACTORS AND CONDITIONS", 38, "contributing_factors"),
    ("FOR VEHICLE DEFECTS", 39, "vehicle_defects"),
    ("FOR WEATHER CONDITION", 40, "weather"),
    ("FOR LIGHT CONDITION", 41, "light"),
    ("FOR ENTERING ROADS", 42, "entering_roads"),
    ("FOR ROADWAY TYPE", 43, "roadway_type"),
    ("FOR ROADWAY ALIGNMENT", 44, "roadway_alignment"),
    ("FOR SURFACE CONDITION", 45, "surface_condition"),
    ("FOR TRAFFIC CONTROL", 46, "traffic_control"),
]

# Entries the PDF wraps over two lines, or that carry trailing reference text.
PATCHES = {
    ("roadway_system", "LR"): "Local Road/Street (Street, Rd., Ave., Blvd., Pl., Trl., Beach, Alley, Boat Ramp)",
    ("sequence_of_events", "8"): "Non-Collision: Cross Median/Centerline",
    ("sequence_of_events", "19"): "Collision With Work Zone Maintenance Equipment",
    ("contributing_factors", "43"): "Fleeing or Evading Police",
    ("contributing_factors", "78"): "Failed to Slow Down or Move Over for Vehicles Displaying Emergency Lights",
    ("ejected", "3"): "Yes, Partial",
    ("dl_restrictions", "O"): "No tractor-trailer CMV",
}

HEADING = re.compile(r"CODE SHEET VALUES? FOR", re.I)
ENTRY = re.compile(r"(?:(?<=\s)|^)([A-Z0-9]{1,4}(?:-\d)?) {0,2}= {0,2}(\S.*?)(?=\s{2,}[A-Z0-9]{1,4}(?:-\d)? {0,2}= {0,2}\S|\s*$)")
STOP = re.compile(r"^\s*(CONDITIONAL FIELD|EXAMPLE|REQUIRED FORMAT|DEFINITIONS?\b|[A-Z ]+ DEFINITIONS|DESCRIPTIONS OF|For motorcycles|TIP:|\d\.\d[\d.]* ?[–-] |•)")


def build(text):
    lines = text.split("\n")
    out, applied = {}, set()
    for i, line in enumerate(lines):
        if i < 330 or not HEADING.search(line):
            continue
        title = re.sub(r"\s+", " ", line).strip().upper()
        match = next((t for t in TABLES if t[0] in title), None)
        if match is None:
            raise SystemExit(f"Unrecognised code table heading at line {i + 1}: {title}")
        _, number, key = match
        values = {}
        for j in range(i + 1, min(i + 120, len(lines))):
            if STOP.match(lines[j]):
                break
            for m in ENTRY.finditer(lines[j]):
                values[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
        if key == "fin_resp_type":  # "Liability Insurance Policy   Texas Transportation Code: Section 601.053"
            values = {c: d.split(" Texas Transportation Code")[0].strip() for c, d in values.items()}
        for (table, code), desc in PATCHES.items():
            if table == key and code in values:
                values[code] = desc
                applied.add((table, code))
        if key in out and out[key]["values"] != values:
            # Some tables are printed twice (road on which crash occurred / intersecting road).
            # Keep the fuller copy; the second roadway system copy uses a different layout.
            if len(values) <= len(out[key]["values"]):
                continue
        out[key] = {"code_sheet": number, "values": values}
    if applied != set(PATCHES):
        raise SystemExit(f"Patches not applied: {set(PATCHES) - applied}")
    missing = [k for _, _, k in TABLES if k not in out]
    if missing:
        raise SystemExit(f"Tables not found in manual: {missing}")
    return out


if __name__ == "__main__":
    src, dest = sys.argv[1], sys.argv[2]
    tables = build(open(src, encoding="utf-8").read())
    doc = {
        "form": "Texas Peace Officer's Crash Report (CR-3)",
        "form_version": "2023",
        "source": "TxDOT CR-100 Instructions to Police for Reporting Crashes, version 29.0 (2025)",
        "source_url": "https://www.txdot.gov/content/dam/docs/division/trf/crash-records/cr100-v29.pdf",
        "tables": dict(sorted(tables.items(), key=lambda kv: kv[1]["code_sheet"])),
    }
    json.dump(doc, open(dest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{len(tables)} tables, {sum(len(t['values']) for t in tables.values())} codes -> {dest}")
