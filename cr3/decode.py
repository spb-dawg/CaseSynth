"""Turn a structured CR-3 record (codes as written on the report) into decoded form.

Input is the JSON structure described in README.md. Reading the PDF into that
structure is a separate step that is not built yet.

Output mirrors the input, with every coded field replaced by
{"code", "meaning", "table", "known"}. Codes missing from the official table are
collected in `issues` instead of being guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import codes

# field name -> code table, per section of the report
ROAD_FIELDS = {
    "roadway_system": "roadway_system",
    "roadway_part": "roadway_part",
    "street_prefix": "direction",
    "street_suffix": "street_suffix",
    "direction_of_traffic": "direction",
    "direction_from_intersection": "direction",
}
UNIT_FIELDS = {
    "unit_desc": "unit_description",
    "veh_color": "vehicle_color",
    "body_style": "body_style",
    "autonomous_unit": "autonomous_unit",
    "autonomous_level": "autonomous_level",
}
LICENSE_FIELDS = {"type": "dl_id_type", "class": "dl_class"}
LICENSE_LIST_FIELDS = {"endorsements": "cdl_endorsements", "restrictions": "dl_restrictions"}
PERSON_FIELDS = {
    "type": "person_type",
    "seat": "seat_position",
    "injury_severity": "injury_severity",
    "ethnicity": "ethnicity",
    "sex": "sex",
    "ejected": "ejected",
    "restraint": "restraint",
    "airbag": "airbag",
    "helmet": "helmet",
    "solicitation": "solicitation",
    "alcohol_specimen": "alcohol_specimen",
    "drug_specimen": "drug_specimen",
    "drug_result": "drug_result",
    "drug_category": "drug_category",
}
CMV_FIELDS = {
    "vehicle_operation": "vehicle_operation",
    "carrier_id_type": "carrier_id_type",
    "vehicle_type": "cmv_vehicle_type",
    "bus_type": "bus_type",
    "hazmat_class": "hazmat_class",
    "cargo_body_type": "cargo_body_type",
}
FACTOR_FIELDS = {
    "contributing": "contributing_factors",
    "may_have_contributed": "contributing_factors",
    # Vehicle defects use their own table. Codes 14 and 98 mean different things in each.
    "defects_contributing": "vehicle_defects",
    "defects_may_have_contributed": "vehicle_defects",
}
CONDITION_FIELDS = {
    "weather": "weather",
    "light": "light",
    "entering_roads": "entering_roads",
    "roadway_type": "roadway_type",
    "roadway_alignment": "roadway_alignment",
    "surface_condition": "surface_condition",
    "traffic_control": "traffic_control",
}

DAMAGE_RATING = re.compile(r"^(?:(\d{1,2})-)?([A-Z]{2,3})-?(\d)$")


@dataclass
class Issue:
    where: str  # path to the field on the report, e.g. "units[1].factors.contributing[0]"
    message: str


@dataclass
class DecodedReport:
    data: dict
    issues: list[Issue] = field(default_factory=list)
    form_version: str = "2023"
    source: str = ""


def _blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


class _Decoder:
    def __init__(self, book: codes.CodeBook):
        self.book = book
        self.issues: list[Issue] = []

    def one(self, table: str, code, where: str):
        if _blank(code):
            return None
        decoded = self.book.lookup(table, code)
        if not decoded.known:
            self.issues.append(Issue(where, f"Code {decoded.code!r} is not in the official {table} table "
                                            f"(code sheet {self.book.code_sheet_number(table)}). "
                                            "Check the report: possible misread, typo, or a different form version."))
        return decoded.as_dict()

    def fields(self, record: dict, mapping: dict, where: str) -> dict:
        out = dict(record)
        for name, table in mapping.items():
            if name in record:
                out[name] = self.one(table, record[name], f"{where}.{name}")
        return out

    def lists(self, record: dict, mapping: dict, where: str) -> dict:
        out = dict(record)
        for name, table in mapping.items():
            if name in record:
                out[name] = [d for i, c in enumerate(record[name] or [])
                             if (d := self.one(table, c, f"{where}.{name}[{i}]")) is not None]
        return out

    def damage_rating(self, text, where: str):
        if _blank(text):
            return None
        raw = str(text).strip().upper()
        special = self.book.table("damage_rating_special")
        if raw in special:
            return {"raw": raw, "special": special[raw]}
        m = DAMAGE_RATING.match(raw)
        if not m:
            self.issues.append(Issue(where, f"Damage rating {raw!r} is not in the XX-ABC-Y format the manual requires."))
            return {"raw": raw}
        force, area, severity = m.groups()
        if force and not 1 <= int(force) <= 12:
            self.issues.append(Issue(where, f"Damage rating {raw!r}: direction of force must be 1-12."))
        if int(severity) > 7:
            self.issues.append(Issue(where, f"Damage rating {raw!r}: severity must be 0-7."))
        return {
            "raw": raw,
            "direction_of_force": f"{int(force)} o'clock" if force else None,
            # Area codes are defined in TxDOT's CR-80 Vehicle Damage Guide, which is not loaded yet.
            "area_code": area,
            "severity": int(severity),
        }

    def unit(self, unit: dict, where: str) -> dict:
        out = self.fields(unit, UNIT_FIELDS, where)
        if "driver_license" in unit:
            w = f"{where}.driver_license"
            out["driver_license"] = self.lists(self.fields(unit["driver_license"], LICENSE_FIELDS, w),
                                               LICENSE_LIST_FIELDS, w)
        if "fin_resp" in unit:
            out["fin_resp"] = self.fields(unit["fin_resp"], {"type": "fin_resp_type"}, f"{where}.fin_resp")
        if "damage_ratings" in unit:
            out["damage_ratings"] = [self.damage_rating(r, f"{where}.damage_ratings[{i}]")
                                     for i, r in enumerate(unit["damage_ratings"] or [])]
        out["persons"] = [self.fields(p, PERSON_FIELDS, f"{where}.persons[{i}]")
                          for i, p in enumerate(unit.get("persons") or [])]
        if unit.get("cmv"):
            cmv = self.lists(self.fields(unit["cmv"], CMV_FIELDS, f"{where}.cmv"),
                             {"sequence_of_events": "sequence_of_events"}, f"{where}.cmv")
            cmv["trailers"] = [self.fields(t, {"type": "trailer_type"}, f"{where}.cmv.trailers[{i}]")
                               for i, t in enumerate(unit["cmv"].get("trailers") or [])]
            out["cmv"] = cmv
        if "factors" in unit:
            out["factors"] = self.lists(unit["factors"], FACTOR_FIELDS, f"{where}.factors")
        return out


def decode(report: dict) -> DecodedReport:
    """Decode a structured CR-3 record. Raises KeyError for a form version with no tables loaded."""
    version = str(report.get("form_version", "2023"))
    book = codes.load(version)
    d = _Decoder(book)
    out = dict(report)
    crash = dict(report.get("crash") or {})
    for road in ("road", "intersecting_road"):
        if road in crash:
            crash[road] = d.fields(crash[road], ROAD_FIELDS, f"crash.{road}")
    out["crash"] = crash
    out["units"] = [d.unit(u, f"units[{i}]") for i, u in enumerate(report.get("units") or [])]
    if "conditions" in report:
        out["conditions"] = d.fields(report["conditions"], CONDITION_FIELDS, "conditions")
    return DecodedReport(data=out, issues=d.issues, form_version=version, source=book.source)
