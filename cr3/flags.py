"""Rules that turn a decoded CR-3 into flags for the first-week case check.

Each flag states a fact found on the report and names the field it came from.
Flags do not say whether a case is viable: that is the attorney's judgment.

Kinds:
  dealbreaker  a fact that can sink or shrink the client's case
  builder      a fact that supports the case or points to another source of recovery
  deadline     evidence or a claim that expires on a date
  verify       the report looks inconsistent, incomplete or misread

Side-dependent facts (fault, impairment, insurance) need to know which unit is
the client's. Without it they are reported as "fact" for the reader to sort.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .decode import DecodedReport

# Deadlines. `basis` is a pointer for the attorney to confirm, not legal advice.
# None of these has been reviewed by a lawyer yet.
DEADLINES = {
    "limitations": ("Two-year filing deadline for personal injury", {"years": 2},
                    "Tex. Civ. Prac. & Rem. Code 16.003. Exceptions and tolling apply."),
    "gov_notice": ("Notice of claim to a governmental unit", {"months": 6},
                   "Tex. Civ. Prac. & Rem. Code 101.101 allows six months; city charters can set shorter periods."),
    "audio_911": ("911 audio may be destroyed", {"days": 30},
                  "State minimum retention for 911 recordings is 30 days (local retention schedule PS). "
                  "Send a preservation and open-records request."),
    "police_video": ("Body and dash camera video may be destroyed", {"days": 90},
                     "State minimum retention is 90 days; San Antonio PD keeps crash video 180 days (Procedure 410). "
                     "An open-records request extends retention."),
    "driver_logs": ("Commercial driver's hours-of-service logs may be destroyed", {"months": 6},
                    "Carriers must keep records of duty status for six months (49 CFR 395.8). "
                    "Send a preservation letter to the carrier."),
}

GIG_KEYWORDS = re.compile(r"\b(uber|lyft|ride[- ]?share|transportation network|tnc|doordash|grubhub|instacart|"
                          r"amazon flex|delivery driver|on the clock|working for)\b", re.I)
EVIDENCE_KEYWORDS = re.compile(r"\b(witness(?:es)?|video|camera|dash ?cam|body ?cam|surveillance|footage|"
                               r"recording|photos?)\b", re.I)
GOV_BODY_STYLES = {"PC", "PM", "FT", "AM", "SB"}
SPEED_FACTORS = {"22", "60", "61"}  # the manual allows only one of these per unit


@dataclass
class Flag:
    kind: str
    title: str
    detail: str
    sources: list[str] = field(default_factory=list)
    unit: int | None = None
    due: date | None = None

    def as_dict(self) -> dict:
        d = {"kind": self.kind, "title": self.title, "detail": self.detail, "sources": self.sources}
        if self.unit is not None:
            d["unit"] = self.unit
        if self.due is not None:
            d["due"] = self.due.isoformat()
        return d


def parse_date(text) -> date | None:
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(text).strip(), fmt).date()
        except ValueError:
            pass
    return None


def _add(start: date, years=0, months=0, days=0) -> date:
    total = start.month - 1 + months + 12 * years
    year, month = start.year + total // 12, total % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day) + timedelta(days=days)


def _code(value) -> str | None:
    return value["code"] if isinstance(value, dict) else None


def _label(value) -> str:
    if not isinstance(value, dict):
        return str(value)
    return f"{value['code']} = {value['meaning']}" if value.get("known") else f"{value['code']} (not in official table)"


def _driver(unit: dict) -> dict | None:
    return next((p for p in unit.get("persons", []) if _code(p.get("type")) in {"1", "5"}), None)


def find_flags(decoded: DecodedReport, client_unit: int | None = None, as_of: date | None = None) -> list[Flag]:
    r = decoded.data
    as_of = as_of or date.today()
    flags: list[Flag] = []
    units = r.get("units", [])
    ident = r.get("identifiers", {})

    def side(unit_num, against_client, for_client):
        """Kind for a fact that hurts whoever it is recorded against."""
        if client_unit is None:
            return "fact"
        return against_client if unit_num == client_unit else for_client

    # --- report quality -------------------------------------------------
    for issue in decoded.issues:
        flags.append(Flag("verify", "Code not in the official table", issue.message, [issue.where]))
    if ident.get("total_units") not in (None, len(units)):
        flags.append(Flag("verify", "Unit count does not match",
                          f"Report header says {ident['total_units']} units; {len(units)} were read. "
                          "A page may be missing (each CR-3 sheet holds two units).", ["identifiers.total_units"]))
    persons_read = sum(len(u.get("persons", [])) for u in units)
    if ident.get("total_persons") not in (None, persons_read):
        flags.append(Flag("verify", "Person count does not match",
                          f"Report header says {ident['total_persons']} persons; {persons_read} were read.",
                          ["identifiers.total_persons"]))
    if ident.get("supplement"):
        flags.append(Flag("verify", "This is a supplement", "The report is marked as a supplement. "
                          "Get the original report and compare what changed.", ["identifiers.supplement"]))
    if r.get("investigator", {}).get("investigation_complete") is False:
        flags.append(Flag("verify", "Investigation not complete", "The officer marked the investigation as not "
                          "complete. Expect a supplemental report (for example lab results) and request it.",
                          ["investigator.investigation_complete"]))
    severities = {_code(p.get("injury_severity")) for u in units for p in u.get("persons", [])}
    if ident.get("fatal") is not None and bool(ident["fatal"]) != ("K" in severities):
        flags.append(Flag("verify", "Fatal box and injury codes disagree", "The FATAL box and the injury severity "
                          "codes do not agree. A death after the report may be on a supplement.",
                          ["identifiers.fatal"]))
    if ident.get("cmv") is not None and bool(ident["cmv"]) != any(u.get("cmv") for u in units):
        flags.append(Flag("verify", "CMV box and CMV section disagree", "The CMV box and the commercial vehicle "
                          "section do not agree. Check the back page for the CMV section.", ["identifiers.cmv"]))

    # --- per unit -------------------------------------------------------
    for i, u in enumerate(units):
        n, w = u.get("unit_num", i + 1), f"units[{i}]"
        driver = _driver(u) or {}
        who = f"Unit {n}" + (f" ({driver['name']})" if driver.get("name") else "")
        f = u.get("factors", {})

        contributing = f.get("contributing", [])
        if contributing:
            flags.append(Flag(side(n, "dealbreaker", "builder"), f"{who}: contributing factor assigned",
                              "Officer's opinion that this unit contributed to the crash: "
                              + "; ".join(_label(c) for c in contributing) + ". Listed in priority order.",
                              [f"{w}.factors.contributing"], n))
        may = f.get("may_have_contributed", [])
        if may:
            flags.append(Flag(side(n, "dealbreaker", "builder"), f"{who}: possible contributing factor",
                              "Officer recorded as may have contributed: " + "; ".join(_label(c) for c in may) + ".",
                              [f"{w}.factors.may_have_contributed"], n))
        listed = [_code(c) for c in contributing]
        if len(SPEED_FACTORS & set(listed)) > 1:
            flags.append(Flag("verify", f"Unit {n}: speed factors conflict", "Factors 22, 60 and 61 cannot be "
                              "assigned to the same unit under TxDOT's rules. The report may be misread or in error.",
                              [f"{w}.factors.contributing"], n))
        if set(listed) & {_code(c) for c in may}:
            flags.append(Flag("verify", f"Unit {n}: factor listed twice", "The same factor appears as both "
                              "contributing and may have contributed, which TxDOT's rules do not allow.",
                              [f"{w}.factors"], n))
        defects = f.get("defects_contributing", []) + f.get("defects_may_have_contributed", [])
        if defects:
            vehicle = " ".join(str(u.get(k, "")) for k in ("veh_year", "veh_make", "veh_model")).strip()
            flags.append(Flag("builder", f"Unit {n}: vehicle defect recorded",
                              "Officer recorded: " + "; ".join(_label(c) for c in defects) + ". Possible claim against "
                              f"the owner, a maintenance provider or the manufacturer. Check recalls for {vehicle or 'the vehicle'} "
                              f"(VIN {u.get('vin') or 'not recorded'}) and preserve the vehicle.", [f"{w}.factors"], n))

        for j, p in enumerate(u.get("persons", [])):
            pw, name = f"{w}.persons[{j}]", p.get("name") or f"person {p.get('person_num', j + 1)}"
            result = p.get("alcohol_result")
            if result not in (None, "") and float(result) > 0:
                flags.append(Flag(side(n, "dealbreaker", "builder"), f"Unit {n}: alcohol result {result}",
                                  f"{name}: alcohol result {result} BAC, specimen {_label(p.get('alcohol_specimen'))}.",
                                  [f"{pw}.alcohol_result"], n))
                if _code(p.get("alcohol_specimen")) in {"4", "96"}:
                    flags.append(Flag("verify", f"Unit {n}: alcohol result without a specimen", "A result is recorded "
                                      "but the specimen type is refused or none.", [f"{pw}.alcohol_specimen"], n))
            elif _code(p.get("alcohol_specimen")) == "4":
                flags.append(Flag(side(n, "dealbreaker", "builder"), f"Unit {n}: alcohol test refused",
                                  f"{name} refused an alcohol specimen.", [f"{pw}.alcohol_specimen"], n))
            if _code(p.get("drug_result")) == "1":
                flags.append(Flag(side(n, "dealbreaker", "builder"), f"Unit {n}: positive drug test",
                                  f"{name}: drug test positive, category {_label(p.get('drug_category'))}.",
                                  [f"{pw}.drug_result"], n))
            sev = _code(p.get("injury_severity"))
            if sev in {"K", "A"}:
                flags.append(Flag("builder" if client_unit in (None, n) else "fact",
                                  f"Unit {n}: {_label(p['injury_severity'])}", f"{name} is coded {_label(p['injury_severity'])}.",
                                  [f"{pw}.injury_severity"], n))
            if client_unit == n:
                if sev == "N":
                    flags.append(Flag("dealbreaker", f"Client unit: {name} coded as not injured", f"{name} is coded N = Not Injured. "
                                      "Injuries reported later will need medical records to overcome this.",
                                      [f"{pw}.injury_severity"], n))
                if _code(p.get("restraint")) == "96":
                    flags.append(Flag("dealbreaker", f"Client unit: {name} recorded with no restraint", f"{name}: restraint 96 = None. "
                                      "Seat belt non-use can be raised to reduce damages.", [f"{pw}.restraint"], n))
                if _code(p.get("helmet")) == "1":
                    flags.append(Flag("dealbreaker", f"Client unit: {name} recorded with no helmet", f"{name}: helmet 1 = Not Worn.",
                                      [f"{pw}.helmet"], n))
                taken = any(d.get("unit_num") == n and d.get("person_num") == p.get("person_num") and d.get("taken_to")
                            for d in r.get("disposition", []))
                if sev in {"A", "B", "C"} and not taken:
                    flags.append(Flag("dealbreaker", f"Client unit: {name} not taken for treatment", f"{name} is coded injured but no "
                                      "transport is recorded. Expect the insurer to argue a gap in treatment.",
                                      ["disposition"], n))

        lic = u.get("driver_license", {})
        if _code(lic.get("type")) == "5":
            flags.append(Flag(side(n, "dealbreaker", "builder"), f"{who}: unlicensed driver",
                              "Driver licence type 5 = Unlicensed.", [f"{w}.driver_license.type"], n))
        restrictions = [c for c in lic.get("restrictions", []) if _code(c) not in {"96", "A"}]
        if restrictions:
            flags.append(Flag(side(n, "verify", "builder"), f"{who}: licence restrictions", "Restrictions on the licence: "
                              + "; ".join(_label(c) for c in restrictions) + ". Check whether the driver was complying.",
                              [f"{w}.driver_license.restrictions"], n))

        proof = str(u.get("fin_resp", {}).get("proof") or "").lower()
        if u.get("hit_and_run"):
            flags.append(Flag(side(n, "fact", "dealbreaker"), f"Unit {n}: hit and run",
                              "This unit left the scene. If the driver is not identified, recovery depends on the "
                              "client's own uninsured motorist coverage.", [f"{w}.hit_and_run"], n))
        elif proof in {"no", "expired"}:
            flags.append(Flag(side(n, "fact", "dealbreaker"), f"{who}: no valid proof of insurance",
                              f"Proof of financial responsibility is marked {proof.upper()}. Check for a policy in "
                              "force and for the client's uninsured or underinsured motorist coverage.",
                              [f"{w}.fin_resp.proof"], n))
        elif proof == "exempt":
            flags.append(Flag("verify", f"{who}: exempt from insurance requirement", "Marked EXEMPT, which usually "
                              f"means a government vehicle. Reason given: {u['fin_resp'].get('name') or 'none'}.",
                              [f"{w}.fin_resp.proof"], n))

        owner = (u.get("owner_lessee") or {}).get("name")
        if owner and driver.get("name") and _norm(owner) != _norm(driver["name"]) and n != client_unit:
            flags.append(Flag("builder", f"Unit {n}: owner is not the driver",
                              f"Driven by {driver['name']}, owned or leased by {owner}. Possible employer liability or "
                              "negligent entrustment, and a second insurance policy.", [f"{w}.owner_lessee.name"], n))

        cmv = u.get("cmv")
        if cmv and n != client_unit:
            carrier = cmv.get("carrier_name") or "carrier not named"
            flags.append(Flag("builder", f"Unit {n}: commercial vehicle",
                              f"{carrier}, ID {_label(cmv.get('carrier_id_type'))} {cmv.get('carrier_id_num') or 'none'}; "
                              f"operation {_label(cmv.get('vehicle_operation'))}; type {_label(cmv.get('vehicle_type'))}; "
                              f"GVWR {cmv.get('gvwr') or 'not recorded'}. Pull the carrier's federal safety and insurance "
                              "records and send a preservation letter (driver file, logs, onboard data, dashcam, "
                              "post-crash drug and alcohol tests).", [f"{w}.cmv"], n))
            if cmv.get("hazmat") or cmv.get("hazmat_released"):
                flags.append(Flag("builder", f"Unit {n}: hazardous material", "Hazmat is recorded for this unit"
                                  + (" and was released." if cmv.get("hazmat_released") else ".")
                                  + " Higher federal insurance minimums apply.", [f"{w}.cmv.hazmat"], n))
        if cmv:
            if _code(cmv.get("vehicle_operation")) == "1" and "K" in {_code(c) for c in lic.get("restrictions", [])}:
                flags.append(Flag(side(n, "dealbreaker", "builder"), f"{who}: intrastate-only licence on an interstate trip",
                                  "Licence restriction K = Intrastate only, but the vehicle operation is coded "
                                  "1 = Interstate Commerce.", [f"{w}.driver_license.restrictions", f"{w}.cmv.vehicle_operation"], n))
            gvwr = cmv.get("gvwr")
            if isinstance(gvwr, (int, float)) and gvwr >= 26001 and _code(lic.get("type")) not in {None, "2"}:
                flags.append(Flag(side(n, "dealbreaker", "builder"), f"{who}: no commercial licence recorded",
                                  f"GVWR is {gvwr} lbs but the licence type is {_label(lic.get('type'))}. "
                                  "Check whether a commercial licence was required.", [f"{w}.driver_license.type", f"{w}.cmv.gvwr"], n))
        government = (_code((cmv or {}).get("vehicle_operation")) == "4" or proof == "exempt" or u.get("emergency")
                      or _code(u.get("body_style")) in GOV_BODY_STYLES)
        if government and n != client_unit:
            flags.append(_deadline("gov_notice", r, as_of, [f"{w}"], n,
                                   prefix=f"Unit {n} appears to be a government vehicle. "))
        if _code(u.get("autonomous_level")) in {"1", "2", "3", "4", "5"}:
            flags.append(Flag("builder", f"Unit {n}: driving automation engaged",
                              f"Automation level {_label(u['autonomous_level'])}. Preserve vehicle data; possible "
                              "manufacturer claim.", [f"{w}.autonomous_level"], n))

    # --- charges ----------------------------------------------------------
    for i, c in enumerate(r.get("charges", [])):
        n = c.get("unit_num")
        flags.append(Flag(side(n, "dealbreaker", "builder"), f"Unit {n}: charge filed",
                          f"{c.get('charge')} (citation {c.get('citation') or 'not recorded'}).", [f"charges[{i}]"], n))

    # --- scene ------------------------------------------------------------
    road, cond = r.get("crash", {}).get("road", {}), r.get("conditions", {})
    if road.get("construction_zone"):
        flags.append(Flag("builder", "Crash in a construction zone", "Construction zone marked"
                          + (", workers present" if road.get("workers_present") else "")
                          + ". Identify the contractor and the traffic control plan.", ["crash.road.construction_zone"]))
    if _code(cond.get("traffic_control")) == "2":
        flags.append(Flag("builder", "Traffic control inoperative", "Traffic control is coded 2 = Inoperative. "
                          "Identify who maintains the signal; the narrative should explain.", ["conditions.traffic_control"]))

    # --- free text ----------------------------------------------------------
    texts = {"narrative": r.get("narrative") or ""}
    for i, u in enumerate(units):
        texts[f"units[{i}].owner_lessee.name"] = (u.get("owner_lessee") or {}).get("name") or ""
        texts[f"units[{i}].fin_resp.name"] = (u.get("fin_resp") or {}).get("name") or ""
    gig = {(m.group(0).lower(), where) for where, t in texts.items() for m in GIG_KEYWORDS.finditer(t)}
    if gig:
        flags.append(Flag("builder", "Possible rideshare or delivery driver",
                          "The CR-3 has no rideshare field. Keyword match only: "
                          + ", ".join(sorted({k for k, _ in gig})) + ". Confirm whether the driver was on the app; "
                          "company coverage depends on the trip stage.", sorted({w for _, w in gig})))
    evidence = sorted({m.group(0).lower() for m in EVIDENCE_KEYWORDS.finditer(texts["narrative"])})
    if evidence:
        flags.append(Flag("builder", "Narrative mentions evidence to secure",
                          "Keyword match: " + ", ".join(evidence) + ". The CR-3 has no witness section, so witnesses "
                          "and video appear only in the narrative.", ["narrative"]))

    # --- deadlines ----------------------------------------------------------
    flags.append(_deadline("limitations", r, as_of, ["crash.date"]))
    flags.append(_deadline("audio_911", r, as_of, ["crash.date"]))
    flags.append(_deadline("police_video", r, as_of, ["crash.date"]))
    if any(u.get("cmv") and u.get("unit_num") != client_unit for u in units):
        flags.append(_deadline("driver_logs", r, as_of, ["crash.date"]))

    order = {"dealbreaker": 0, "builder": 1, "fact": 2, "deadline": 3, "verify": 4}
    return sorted((f for f in flags if f), key=lambda f: (order[f.kind], f.due or date.max))


def _norm(name: str) -> str:
    return " ".join(sorted(re.sub(r"[^a-z ]", " ", name.lower()).split()))


def _deadline(key, report, as_of, sources, unit=None, prefix="") -> Flag | None:
    title, offset, basis = DEADLINES[key]
    crash = parse_date(report.get("crash", {}).get("date"))
    if crash is None:
        return Flag("verify", f"{title}: no crash date", "The crash date could not be read, so this deadline "
                    "was not calculated.", ["crash.date"], unit)
    due = _add(crash, **offset)
    left = (due - as_of).days
    status = f"{left} days left" if left >= 0 else f"PASSED {-left} days ago"
    return Flag("deadline", title, f"{prefix}{due.isoformat()} ({status} as of {as_of.isoformat()}). {basis}",
                sources, unit, due)
