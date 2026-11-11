"""FMCSA SAFER Company Snapshot: a motor carrier's public federal record.

https://safer.fmcsa.dot.gov/CompanySnapshot.aspx

This reads the public snapshot web page, which needs no account. FMCSA also
offers an API (QCMobile) that needs a free WebKey; moving to it is the sturdier
long-term route, since a page layout change would break this parser.

Inspection and crash counts cover the 24 months before the snapshot date. Crash
counts are involvement only, with no finding of fault.
"""
from __future__ import annotations

import html
import re

from .http import LookupFailed, quote

SNAPSHOT = ("https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&query_type=queryCarrierSnapshot"
            "&query_param=USDOT&query_string={dot}")


def _text(page: str) -> str:
    page = re.sub(r"(?is)<(script|style).*?</\1>|<!--.*?-->", "", page)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)).replace("\xa0", " "))


def _int(text: str) -> int:
    return int(text.replace(",", ""))


def parse_snapshot(page: str) -> dict | None:
    """Parse a snapshot page. Returns None when FMCSA has no record for the number."""
    t = _text(page)
    if "Record Not Found" in t or "Record Inactive" in t:
        return None

    def find(pattern):
        m = re.search(pattern, t)
        if not m:
            raise LookupFailed("FMCSA snapshot page layout was not recognised")
        return [g.strip() for g in m.groups()]

    name, dba, address = find(r"Legal Name: (.+?) DBA Name: (.*?) Physical Address: (.+?) Phone:")
    status, oos_date = find(r"USDOT Status: ([A-Z\- ]+?) Out of Service Date: (\S+)")
    (authority,) = find(r"Operating Authority Status: (.+?)(?: \*Please Note| For Licensing| MC/MX/FF)")
    units, drivers = find(r"Power Units: ([\d,]*) .*?Drivers: ([\d,]*)")
    as_of, total = find(r"US Inspection results for 24 months prior to: (\S+) Total Inspections: ([\d,]+)")
    insp = find(r"Inspections ([\d,]+) ([\d,]+) ([\d,]+) [\d,]+ Out of Service ([\d,]+) ([\d,]+) ([\d,]+) [\d,]+ "
                r"Out of Service % ([\d.]+)% ([\d.]+)% ([\d.]+)%")
    national = find(r"Nat'l Average % as of DATE \S+ ?\* ([\d.]+)% ([\d.]+)% ([\d.]+)%")
    crashes = find(r"Crashes: Type Fatal Injury Tow Total Crashes ([\d,]+) ([\d,]+) ([\d,]+) ([\d,]+)")
    rating = re.search(r"Rating Date: (\S*) Review Date: (\S*) Rating: (.+?) Type:", t)
    (entity,) = find(r"Entity Type: (\S+)")
    mc = re.search(r"MC/MX/FF Number\(s\): ((?:[A-Z]{2}-\d+ ?)+)", t)

    kinds = ("vehicle", "driver", "hazmat")
    return {
        "legal_name": name,
        "dba_name": dba or None,
        "address": address,
        "entity_type": entity,
        "usdot_status": status,
        "out_of_service_date": None if oos_date == "None" else oos_date,
        "operating_authority": authority,
        "mc_numbers": mc.group(1).split() if mc else [],
        "power_units": _int(units) if units else None,
        "drivers": _int(drivers) if drivers else None,
        "as_of": as_of,
        "total_inspections": _int(total),
        "inspections": {k: {"count": _int(insp[i]), "out_of_service": _int(insp[i + 3]),
                            "oos_rate": float(insp[i + 6]), "national_oos_rate": float(national[i])}
                        for i, k in enumerate(kinds)},
        "crashes": dict(zip(("fatal", "injury", "tow", "total"), map(_int, crashes))),
        "safety_rating": rating.group(3).strip() if rating and rating.group(3).strip() != "None" else None,
        "rating_date": (rating.group(1) or None) if rating and rating.group(1) != "None" else None,
    }


def carrier_snapshot(dot_number, fetch) -> dict | None:
    digits = re.sub(r"\D", "", str(dot_number))
    if not digits:
        raise LookupFailed(f"{dot_number!r} is not a USDOT number")
    snapshot = parse_snapshot(fetch(SNAPSHOT.format(dot=quote(digits))))
    if snapshot is not None:
        snapshot["usdot"] = digits
    return snapshot
