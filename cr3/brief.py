"""Render a decoded CR-3 and its flags as a Markdown brief for a paralegal."""
from __future__ import annotations

from .decode import DecodedReport
from .flags import Flag

SECTIONS = [
    ("dealbreaker", "Possible dealbreakers"),
    ("builder", "Case builders"),
    ("fact", "Fault and coverage facts (client unit not specified)"),
    ("deadline", "Deadlines"),
    ("verify", "Check the report"),
]


def _v(value) -> str:
    """Show a field value: decoded codes as 'code = meaning', blanks as a dash."""
    if value is None or value == "" or value == []:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict) and "code" in value:
        return f"{value['code']} = {value['meaning']}" if value["known"] else f"**{value['code']} = NOT IN OFFICIAL TABLE**"
    if isinstance(value, dict) and "raw" in value:  # damage rating
        if "special" in value:
            return f"{value['raw']} = {value['special']}"
        if "severity" not in value:
            return f"**{value['raw']} (unreadable format)**"
        force = f"force from {value['direction_of_force']}, " if value["direction_of_force"] else ""
        return f"{value['raw']} ({force}area code {value['area_code']}, severity {value['severity']} of 7)"
    if isinstance(value, list):
        return "; ".join(_v(v) for v in value)
    return str(value)


def _rows(pairs) -> list[str]:
    return [f"- **{label}:** {_v(value)}" for label, value in pairs if value not in (None, "", [])]


def _road(road: dict) -> str:
    parts = [road.get("block_num"), _code(road.get("street_prefix")), road.get("street_name"),
             _code(road.get("street_suffix"))]
    street = " ".join(str(p) for p in parts if p)
    hwy = f"{_v(road.get('roadway_system'))} {road.get('hwy_num') or ''}".strip() if road.get("roadway_system") else ""
    return ", ".join(p for p in (hwy, street) if p) or "—"


def _code(value):
    return value["code"] if isinstance(value, dict) else value


def render_brief(decoded: DecodedReport, flags: list[Flag], client_unit: int | None = None) -> str:
    r = decoded.data
    ident, crash = r.get("identifiers", {}), r.get("crash", {})
    out = [f"# Crash report brief: {ident.get('crash_id') or ident.get('case_id') or 'unidentified report'}", ""]
    out += [f"Texas CR-3, form version {decoded.form_version}. Client: "
            + (f"Unit {client_unit}." if client_unit else "not specified.")
            + " Every item below is a fact read from the report with the field it came from. "
              "Contributing factors are the officer's opinion. Verify against the report before relying on anything here.", ""]

    for kind, heading in SECTIONS:
        group = [f for f in flags if f.kind == kind]
        if not group:
            continue
        out += [f"## {heading}", ""]
        for f in group:
            out.append(f"- **{f.title}.** {f.detail} _(source: {', '.join(f.sources)})_")
        out.append("")

    out += ["## Crash", ""]
    out += _rows([
        ("Date and time", f"{crash.get('date') or '—'} at {crash.get('time') or '—'}"),
        ("Location", f"{crash.get('city') or '—'}, {crash.get('county') or '—'} County"),
        ("Road", _road(crash.get("road", {}))),
        ("Roadway part", crash.get("road", {}).get("roadway_part")),
        ("Speed limit", crash.get("road", {}).get("speed_limit")),
        ("Intersecting road", _road(crash["intersecting_road"]) if crash.get("intersecting_road") else None),
        ("Fatal", ident.get("fatal")), ("Commercial vehicle", ident.get("cmv")),
        ("School bus", ident.get("school_bus")), ("Active school zone", ident.get("active_school_zone")),
    ])
    out.append("")

    cond = r.get("conditions", {})
    if cond:
        out += ["## Conditions", ""]
        out += _rows([("Weather", cond.get("weather")), ("Light", cond.get("light")),
                      ("Surface", cond.get("surface_condition")), ("Traffic control", cond.get("traffic_control")),
                      ("Roadway type", cond.get("roadway_type")), ("Alignment", cond.get("roadway_alignment")),
                      ("Entering roads", cond.get("entering_roads"))])
        out.append("")

    for u in r.get("units", []):
        n = u.get("unit_num")
        out += [f"## Unit {n}" + (" (client)" if n == client_unit else ""), ""]
        lic, fr, own, f = u.get("driver_license", {}), u.get("fin_resp", {}), u.get("owner_lessee") or {}, u.get("factors", {})
        vehicle = " ".join(str(u.get(k) or "") for k in ("veh_year", "veh_make", "veh_model")).strip()
        out += _rows([
            ("Unit type", u.get("unit_desc")), ("Vehicle", vehicle), ("Body style", u.get("body_style")),
            ("Colour", u.get("veh_color")), ("VIN", u.get("vin")),
            ("Plate", f"{u.get('lp_state') or ''} {u.get('lp_num') or ''}".strip()),
            ("Parked", u.get("parked")), ("Hit and run", u.get("hit_and_run")),
            ("Licence", "; ".join(x for x in (_v(lic.get("type")), "class " + _v(lic.get("class")),
                                              "state " + str(lic.get("state") or "—")) if lic) if lic else None),
            ("Endorsements", lic.get("endorsements")), ("Restrictions", lic.get("restrictions")),
            ("Owner or lessee", f"{own.get('name')} ({own.get('role') or 'role not marked'})" if own.get("name") else None),
            ("Proof of insurance", str(fr.get("proof")).upper() if fr.get("proof") else None),
            ("Insurance type", fr.get("type")), ("Insurer", fr.get("name")), ("Policy number", fr.get("number")),
            ("Damage ratings", u.get("damage_ratings")), ("Towed to", u.get("towed_to")),
            ("Contributing factors", f.get("contributing")), ("May have contributed", f.get("may_have_contributed")),
            ("Vehicle defects, contributing", f.get("defects_contributing")),
            ("Vehicle defects, may have contributed", f.get("defects_may_have_contributed")),
        ])
        cmv = u.get("cmv")
        if cmv:
            out += ["", "**Commercial vehicle section**", ""]
            out += _rows([
                ("Carrier", cmv.get("carrier_name")), ("Carrier address", cmv.get("carrier_address")),
                ("Carrier ID", f"{_v(cmv.get('carrier_id_type'))}: {cmv.get('carrier_id_num') or '—'}"),
                ("Operation", cmv.get("vehicle_operation")), ("Vehicle type", cmv.get("vehicle_type")),
                ("Cargo body", cmv.get("cargo_body_type")), ("GVWR", cmv.get("gvwr")),
                ("Disabling damage", cmv.get("disabling_damage")), ("Hazmat class", cmv.get("hazmat_class")),
                ("Hazmat released", cmv.get("hazmat_released")), ("Sequence of events", cmv.get("sequence_of_events")),
                ("Trailers", [f"unit {t.get('unit_num')}: {_v(t.get('type'))}" for t in cmv.get("trailers", [])]),
            ])
        for p in u.get("persons", []):
            out += ["", f"**Person {p.get('person_num')}: {p.get('name') or 'name not recorded'}**", ""]
            out += _rows([
                ("Role", p.get("type")), ("Seat", p.get("seat")), ("Age", p.get("age")),
                ("Injury severity", p.get("injury_severity")), ("Ejected", p.get("ejected")),
                ("Restraint", p.get("restraint")), ("Airbag", p.get("airbag")), ("Helmet", p.get("helmet")),
                ("Alcohol specimen", p.get("alcohol_specimen")), ("Alcohol result", p.get("alcohol_result")),
                ("Drug specimen", p.get("drug_specimen")), ("Drug result", p.get("drug_result")),
                ("Drug category", p.get("drug_category")), ("Solicitation", p.get("solicitation")),
            ])
        out.append("")

    if r.get("charges"):
        out += ["## Charges", ""]
        out += [f"- Unit {c.get('unit_num')}, person {c.get('person_num')}: {c.get('charge')} "
                f"(citation {c.get('citation') or '—'})" for c in r["charges"]]
        out.append("")
    if r.get("disposition"):
        out += ["## Injured taken to", ""]
        out += [f"- Unit {d.get('unit_num')}, person {d.get('person_num')}: {d.get('taken_to') or '—'} "
                f"by {d.get('taken_by') or '—'}" for d in r["disposition"]]
        out.append("")
    if r.get("narrative"):
        out += ["## Officer's narrative", "", "> " + r["narrative"].strip().replace("\n", "\n> "), ""]

    inv = r.get("investigator", {})
    if inv:
        out += ["## Investigator", ""]
        out += _rows([("Name", inv.get("name")), ("ID", inv.get("id")), ("Agency", inv.get("agency")),
                      ("Report date", inv.get("report_date")), ("Investigation complete", inv.get("investigation_complete"))])
        out.append("")
    out += ["---", f"Codes decoded from: {decoded.source}. Deadline rules and legal notes have not been reviewed by an attorney."]
    return "\n".join(out) + "\n"
