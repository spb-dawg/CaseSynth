"""Run outside lookups for a decoded report and turn the results into flags.

Lookups send the VIN and USDOT number from the report to federal services
(NHTSA and FMCSA). No names, addresses or other personal details are sent.
A lookup that fails is recorded and flagged; it never stops the brief.
"""
from __future__ import annotations

import re

from ..decode import DecodedReport
from ..flags import Flag
from . import fmcsa, nhtsa
from .http import LookupFailed
from .http import fetch as http_fetch

# CR-3 vehicle defect code -> words to look for in an NHTSA recall component
DEFECT_COMPONENTS = {
    "5": ("LIGHTING",), "6": ("LIGHTING",), "7": ("LIGHTING",), "8": ("LIGHTING",),
    "9": ("BRAKE",), "10": ("BRAKE",), "11": ("STEERING",), "12": ("TIRE", "WHEEL"),
    "13": ("HITCH", "COUPLING"),
}


def _code(value):
    return value["code"] if isinstance(value, dict) else None


def _same(a, b) -> bool:
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", str(s or "").upper())
    return bool(norm(a)) and (norm(a) in norm(b) or norm(b) in norm(a))


def enrich(decoded: DecodedReport, fetch=http_fetch) -> list[dict]:
    """Return one lookup record per unit that has a VIN or a USDOT number."""
    results = []
    for i, u in enumerate(decoded.data.get("units", [])):
        rec = {"unit_num": u.get("unit_num", i + 1), "where": f"units[{i}]", "errors": []}

        vin = (u.get("vin") or "").strip()
        if vin:
            try:
                v = rec["vin"] = nhtsa.decode_vin(vin, fetch)
                # A clean decode gives NHTSA's own make and model names. If the VIN has errors its
                # decoded year and model cannot be trusted, so use what the officer wrote instead.
                source = v if v["clean"] else {}
                make, model, year = (source.get("make") or u.get("veh_make"), source.get("model") or u.get("veh_model"),
                                     source.get("year") or u.get("veh_year"))
                if make and model and year:
                    rec["vehicle"] = {"make": make, "model": model, "year": year}
                    rec["recalls"] = nhtsa.recalls(make, model, year, fetch)
                    rec["complaints"] = nhtsa.complaints(make, model, year, fetch)
            except (LookupFailed, ValueError, KeyError, IndexError) as exc:
                rec["errors"].append(f"NHTSA lookup failed: {exc}")

        cmv = u.get("cmv") or {}
        if _code(cmv.get("carrier_id_type")) == "1" and cmv.get("carrier_id_num"):
            try:
                rec["carrier"] = fmcsa.carrier_snapshot(cmv["carrier_id_num"], fetch)
                rec["carrier_searched"] = str(cmv["carrier_id_num"])
            except LookupFailed as exc:
                rec["errors"].append(f"FMCSA lookup failed: {exc}")

        if len(rec) > 3 or rec["errors"]:
            results.append(rec)
    return results


def lookup_flags(decoded: DecodedReport, lookups: list[dict], client_unit: int | None = None) -> list[Flag]:
    flags: list[Flag] = []
    units = {u.get("unit_num", i + 1): u for i, u in enumerate(decoded.data.get("units", []))}
    for rec in lookups:
        n, w, u = rec["unit_num"], rec["where"], units[rec["unit_num"]]
        for error in rec["errors"]:
            flags.append(Flag("verify", f"Unit {n}: outside lookup did not complete", error + ". Run it again or check by hand.",
                              [w], n))

        v = rec.get("vin")
        if v:
            if not v["clean"]:
                flags.append(Flag("verify", f"Unit {n}: VIN did not decode cleanly",
                                  f"NHTSA reports: {v['error_text']}. The VIN may be misread or mistyped on the report.",
                                  [f"{w}.vin"], n))
            mismatches = [] if not v["clean"] else [f"{label} is {reported} on the report but {found} from the VIN"
                          for label, reported, found in (("make", u.get("veh_make"), v["make"]),
                                                         ("year", u.get("veh_year"), v["year"]))
                          if reported and found and not _same(reported, found)]
            if mismatches:
                flags.append(Flag("verify", f"Unit {n}: vehicle does not match its VIN", "; ".join(mismatches) + ".",
                                  [f"{w}.vin", f"{w}.veh_make", f"{w}.veh_year"], n))

        recalls = rec.get("recalls") or []
        if recalls:
            car = rec["vehicle"]
            name = f"{car['year']} {car['make']} {car['model']}"
            defects = {_code(c) for key in ("defects_contributing", "defects_may_have_contributed")
                       for c in u.get("factors", {}).get(key, [])}
            words = {w_ for d in defects for w_ in DEFECT_COMPONENTS.get(d, ())}
            matching = [r for r in recalls if any(word in (r["component"] or "").upper() for word in words)]
            if matching:
                flags.append(Flag("builder", f"Unit {n}: recall matches the recorded vehicle defect",
                                  f"The officer recorded a vehicle defect, and NHTSA lists {len(matching)} recall(s) for the "
                                  f"{name} on the same system: "
                                  + "; ".join(f"{r['campaign']} ({r['component']})" for r in matching)
                                  + ". Preserve the vehicle and confirm this VIN's recall status.",
                                  [f"{w}.factors", f"{w}.vin"], n))
            flags.append(Flag("builder", f"Unit {n}: {len(recalls)} recall(s) for this vehicle line",
                              f"NHTSA lists {len(recalls)} recall(s) for the {name}: "
                              + "; ".join(sorted({r["component"] or "component not stated" for r in recalls}))
                              + ". These apply to the model line; confirm whether this VIN is affected and repaired.",
                              [f"{w}.vin"], n))

        if "carrier" in rec:
            c = rec["carrier"]
            if c is None:
                flags.append(Flag("verify", f"Unit {n}: USDOT number not found",
                                  f"FMCSA has no record for USDOT {rec['carrier_searched']}. The number may be misread, or the "
                                  "carrier may be registered only in Texas.", [f"{w}.cmv.carrier_id_num"], n))
                continue
            src = [f"{w}.cmv.carrier_id_num"]
            reported = (u.get("cmv") or {}).get("carrier_name")
            if reported and not (_same(reported, c["legal_name"]) or _same(reported, c["dba_name"])):
                flags.append(Flag("verify", f"Unit {n}: carrier name does not match the USDOT number",
                                  f"The report names {reported}; FMCSA lists USDOT {c['usdot']} as {c['legal_name']}"
                                  + (f" (DBA {c['dba_name']})" if c["dba_name"] else "")
                                  + ". Either the number is wrong or a second company is involved.", src, n))
            if n == client_unit:
                continue
            if c["usdot_status"] != "ACTIVE" or c["out_of_service_date"]:
                flags.append(Flag("builder", f"Unit {n}: carrier is not in active status",
                                  f"FMCSA lists USDOT status {c['usdot_status']}"
                                  + (f", out of service since {c['out_of_service_date']}" if c["out_of_service_date"] else "")
                                  + ".", src, n))
            if c["operating_authority"].upper().startswith("NOT AUTHORIZED") and \
                    _code((u.get("cmv") or {}).get("vehicle_operation")) == "1":
                flags.append(Flag("builder", f"Unit {n}: no interstate operating authority on file",
                                  "The report codes this trip as interstate commerce, and FMCSA lists the carrier as NOT "
                                  "AUTHORIZED. This does not apply to private carriers; check which this is.", src, n))
            high = [f"{kind} {i['oos_rate']}% (national average {i['national_oos_rate']}%, {i['out_of_service']} of {i['count']} inspections)"
                    for kind, i in c["inspections"].items() if i["count"] and i["oos_rate"] > i["national_oos_rate"]]
            if high:
                flags.append(Flag("builder", f"Unit {n}: carrier out-of-service rate above the national average",
                                  f"{c['legal_name']}, 24 months to {c['as_of']}: " + "; ".join(high) + ".", src, n))
            if c["safety_rating"] and c["safety_rating"].lower() != "satisfactory":
                flags.append(Flag("builder", f"Unit {n}: carrier safety rating is {c['safety_rating']}",
                                  f"FMCSA safety rating {c['safety_rating']}, dated {c['rating_date'] or 'not stated'}.", src, n))
            flags.append(Flag("builder", f"Unit {n}: carrier federal record",
                              f"{c['legal_name']} (USDOT {c['usdot']}): {c['power_units']} power units, {c['drivers']} drivers. "
                              f"In the 24 months to {c['as_of']}: {c['total_inspections']} inspections and "
                              f"{c['crashes']['total']} reported crashes ({c['crashes']['fatal']} fatal, "
                              f"{c['crashes']['injury']} injury). Crash counts show involvement, not fault.", src, n))
    return flags
