"""FMCSA: a motor carrier's public federal record, from two sources.

Primary: the QCMobile API, https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi
  Needs a free WebKey, read from the FMCSA_WEBKEY environment variable. Returns JSON,
  so a page redesign cannot break it, and it carries insurance on file.

Fallback: the SAFER Company Snapshot page, https://safer.fmcsa.dot.gov/CompanySnapshot.aspx
  Needs no account. Used when there is no key, or when the API call fails for any
  reason. A layout change would break this parser, which then fails loudly.

Both sources are reduced to the same record so flags and the brief do not care which
answered; `source` says which did. Inspection and crash counts cover the 24 months
before the snapshot date. Crash counts are involvement only, with no finding of fault.
"""
from __future__ import annotations

import html
import json
import re

from .http import HttpError, LookupFailed, quote

SNAPSHOT = ("https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&query_type=queryCarrierSnapshot"
            "&query_param=USDOT&query_string={dot}")
API = "https://mobile.fmcsa.dot.gov/qc/services/carriers/{dot}?webKey={key}"
API_DOCKETS = "https://mobile.fmcsa.dot.gov/qc/services/carriers/{dot}/docket-numbers?webKey={key}"

SOURCE_API = "FMCSA QCMobile API"
SOURCE_SAFER = "FMCSA SAFER snapshot page"

KINDS = ("vehicle", "driver", "hazmat")
SAFETY_RATINGS = {"S": "Satisfactory", "C": "Conditional", "U": "Unsatisfactory"}
STATUS_CODES = {"A": "ACTIVE", "I": "INACTIVE"}


# ----------------------------------------------------------------------------- SAFER page

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

    return {
        "source": SOURCE_SAFER,
        "legal_name": name,
        "dba_name": dba or None,
        "address": address,
        "entity_type": entity,
        "usdot_status": status,
        "out_of_service_date": None if oos_date == "None" else oos_date,
        "allowed_to_operate": None,
        "operating_authority": authority,
        "mc_numbers": mc.group(1).split() if mc else [],
        "power_units": _int(units) if units else None,
        "drivers": _int(drivers) if drivers else None,
        "as_of": as_of,
        "total_inspections": _int(total),
        "inspections": {k: {"count": _int(insp[i]), "out_of_service": _int(insp[i + 3]),
                            "oos_rate": float(insp[i + 6]), "national_oos_rate": float(national[i])}
                        for i, k in enumerate(KINDS)},
        "crashes": dict(zip(("fatal", "injury", "tow", "total"), map(_int, crashes))),
        "safety_rating": rating.group(3).strip() if rating and rating.group(3).strip() != "None" else None,
        "rating_date": (rating.group(1) or None) if rating and rating.group(1) != "None" else None,
        "insurance": None,
    }


def carrier_snapshot(dot_number, fetch) -> dict | None:
    """SAFER page lookup. Returns None when FMCSA has no record for the number."""
    digits = _digits(dot_number)
    snapshot = parse_snapshot(fetch(SNAPSHOT.format(dot=quote(digits))))
    if snapshot is not None:
        snapshot["usdot"] = digits
    return snapshot


# ----------------------------------------------------------------------------- QCMobile API

def _num(value, kind=float):
    if value in (None, ""):
        return None
    try:
        return kind(str(value).replace(",", ""))
    except ValueError:
        return None


def _authority_text(c: dict) -> str:
    """Reduce the API's three authority status letters to SAFER's wording."""
    statuses = {k: (c.get(f"{k}AuthorityStatus") or "N").upper() for k in ("common", "contract", "broker")}
    active = [k for k, s in statuses.items() if s == "A"]
    if active:
        return "AUTHORIZED (" + ", ".join(f"{k} carrier" if k != "broker" else "broker" for k in active) + ")"
    if any(s == "I" for s in statuses.values()):
        return "NOT AUTHORIZED (authority inactive)"
    return "NOT AUTHORIZED (no authority on file)"


def parse_api(body: str, dockets: str | None = None) -> dict | None:
    """Parse a QCMobile carrier response. Returns None when FMCSA has no record for the number."""
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise LookupFailed("FMCSA API did not return JSON") from exc
    if not isinstance(data, dict):
        raise LookupFailed("FMCSA API response was not recognised")
    content = data.get("content")
    if content is None:
        return None
    if isinstance(content, str):  # error text, e.g. "Webkey not found"
        raise LookupFailed(f"FMCSA API: {content}")
    c = content.get("carrier") if isinstance(content, dict) else None
    if not isinstance(c, dict) or "legalName" not in c:
        raise LookupFailed("FMCSA API response was not recognised")

    mc_numbers = []
    if dockets:
        try:
            for row in (json.loads(dockets).get("content") or []):
                if row.get("docketNumber") is not None:
                    mc_numbers.append(f"{row.get('prefix') or 'MC'}-{row['docketNumber']}")
        except (ValueError, AttributeError, TypeError):
            pass  # docket numbers are informational; a bad answer must not sink the record

    rating = (c.get("safetyRating") or "").strip() or None
    status = (c.get("statusCode") or "").strip().upper()
    address = ", ".join(p for p in (c.get("phyStreet"), c.get("phyCity"),
                                    " ".join(q for q in (c.get("phyState"), c.get("phyZipcode")) if q)) if p)
    as_of = (c.get("snapshotDate") or data.get("retrievalDate") or "")[:10] or None
    census = c.get("censusTypeId") or {}

    def inspections(kind):
        count = _num(c.get(f"{kind}Insp"), int) or 0
        oos = _num(c.get(f"{kind}OosInsp"), int) or 0
        rate = _num(c.get(f"{kind}OosRate"))
        return {"count": count, "out_of_service": oos,
                "oos_rate": rate if rate is not None else (round(100 * oos / count, 2) if count else 0.0),
                "national_oos_rate": _num(c.get(f"{kind}OosRateNationalAverage"))}

    insurance = None
    if c.get("bipdInsuranceRequired") is not None or c.get("bipdInsuranceOnFile") is not None:
        thousands = lambda v: None if _num(v, int) is None else _num(v, int) * 1000
        insurance = {"bipd_required": (c.get("bipdInsuranceRequired") or "").upper() == "Y",
                     "bipd_required_amount": thousands(c.get("bipdRequiredAmount")),
                     "bipd_on_file": thousands(c.get("bipdInsuranceOnFile")),
                     "cargo_on_file": thousands(c.get("cargoInsuranceOnFile")),
                     "bond_on_file": thousands(c.get("bondInsuranceOnFile"))}

    return {
        "source": SOURCE_API,
        "legal_name": c["legalName"],
        "dba_name": c.get("dbaName") or None,
        "address": address,
        "entity_type": census.get("censusTypeDesc") or census.get("censusType"),
        "usdot_status": STATUS_CODES.get(status, status or "UNKNOWN"),
        "out_of_service_date": (c.get("oosDate") or None) and str(c["oosDate"])[:10],
        "allowed_to_operate": {"Y": True, "N": False}.get((c.get("allowedToOperate") or "").upper()),
        "operating_authority": _authority_text(c),
        "mc_numbers": mc_numbers,
        "power_units": _num(c.get("totalPowerUnits"), int),
        "drivers": _num(c.get("totalDrivers"), int),
        "as_of": as_of,
        "total_inspections": None,  # the API gives vehicle, driver and hazmat counts, not SAFER's combined total
        "inspections": {k: inspections(k) for k in KINDS},
        "crashes": {"fatal": _num(c.get("fatalCrash"), int) or 0, "injury": _num(c.get("injCrash"), int) or 0,
                    "tow": _num(c.get("towawayCrash"), int) or 0, "total": _num(c.get("crashTotal"), int) or 0},
        "safety_rating": SAFETY_RATINGS.get(rating.upper(), rating) if rating else None,
        "rating_date": (c.get("safetyRatingDate") or None) and str(c["safetyRatingDate"])[:10],
        "insurance": insurance,
        "mcs150_outdated": (c.get("mcs150Outdated") or "").upper() == "Y" or None,
    }


def carrier_api(dot_number, fetch, webkey: str) -> dict | None:
    """QCMobile API lookup. Returns None when FMCSA has no record for the number."""
    digits = _digits(dot_number)
    if not webkey or not webkey.strip():
        raise LookupFailed("FMCSA API: no WebKey")
    key = quote(webkey.strip())
    try:
        body = fetch(API.format(dot=quote(digits), key=key))
    except HttpError as exc:
        if exc.status == 404 and "webkey" in exc.body.lower():
            raise LookupFailed("FMCSA API rejected the WebKey; check FMCSA_WEBKEY") from exc
        raise
    dockets = None
    try:
        dockets = fetch(API_DOCKETS.format(dot=quote(digits), key=key))
    except LookupFailed:
        pass
    record = parse_api(body, dockets)
    if record is not None:
        record["usdot"] = digits
    return record


# ----------------------------------------------------------------------------- entry point

def _digits(dot_number) -> str:
    digits = re.sub(r"\D", "", str(dot_number))
    if not digits:
        raise LookupFailed(f"{dot_number!r} is not a USDOT number")
    return digits


def carrier_record(dot_number, fetch, webkey: str | None = None) -> tuple[dict | None, str | None]:
    """Look a carrier up: the API when a key is given, else (or on API failure) the SAFER page.

    Returns (record, note). The record is None when FMCSA has no record for the number.
    The note says why the API was not used, or None when it was. A failure of the
    fallback raises LookupFailed.
    """
    _digits(dot_number)  # reject a non-number before any request
    note = None
    if webkey:
        try:
            return carrier_api(dot_number, fetch, webkey), None
        except (LookupFailed, KeyError, TypeError) as exc:
            note = f"{exc}; used the SAFER snapshot page instead"
    return carrier_snapshot(dot_number, fetch), note
