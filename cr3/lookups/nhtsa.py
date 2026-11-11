"""NHTSA public APIs: VIN decoding, recalls and owner complaints. Free, no key.

https://vpic.nhtsa.dot.gov/api/  and  https://api.nhtsa.gov/

Recalls and complaints are returned for a make, model and year. They show that a
recall exists for that vehicle line, not that this particular vehicle is affected
or unrepaired. Confirm a specific VIN at nhtsa.gov/recalls.
"""
from __future__ import annotations

import json
from collections import Counter

from .http import quote

VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
RECALLS = "https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}"
COMPLAINTS = "https://api.nhtsa.gov/complaints/complaintsByVehicle?make={make}&model={model}&modelYear={year}"


def decode_vin(vin: str, fetch) -> dict:
    row = json.loads(fetch(VPIC.format(vin=quote(vin.strip().upper()))))["Results"][0]
    codes = [c.strip() for c in str(row.get("ErrorCode") or "0").split(",")]
    return {
        "vin": vin.strip().upper(),
        "make": row.get("Make") or None,
        "model": row.get("Model") or None,
        "year": int(row["ModelYear"]) if str(row.get("ModelYear") or "").isdigit() else None,
        "manufacturer": row.get("Manufacturer") or None,
        "body_class": row.get("BodyClass") or None,
        "vehicle_type": row.get("VehicleType") or None,
        "gvwr_class": row.get("GVWR") or None,
        "clean": codes == ["0"],
        "error_text": None if codes == ["0"] else (row.get("ErrorText") or "").strip(),
    }


def _iso(text):
    """NHTSA prints recall dates as DD/MM/YYYY; return YYYY-MM-DD to avoid misreading."""
    parts = str(text or "").split("/")
    return f"{parts[2]}-{parts[1]}-{parts[0]}" if len(parts) == 3 else text


def recalls(make: str, model: str, year: int, fetch) -> list[dict]:
    data = json.loads(fetch(RECALLS.format(make=quote(make), model=quote(model), year=quote(year))))
    return [{
        "campaign": r.get("NHTSACampaignNumber"),
        "component": r.get("Component"),
        "summary": r.get("Summary"),
        "consequence": r.get("Consequence"),
        "remedy": r.get("Remedy"),
        "received": _iso(r.get("ReportReceivedDate")),
        "park_it": bool(r.get("parkIt")),
    } for r in data.get("results", [])]


def complaints(make: str, model: str, year: int, fetch) -> dict:
    data = json.loads(fetch(COMPLAINTS.format(make=quote(make), model=quote(model), year=quote(year))))
    rows = data.get("results", [])
    components = Counter(part.strip() for r in rows for part in str(r.get("components") or "").split(",") if part.strip())
    return {
        "total": len(rows),
        "with_crash": sum(1 for r in rows if r.get("crash")),
        "with_fire": sum(1 for r in rows if r.get("fire")),
        "injuries": sum(int(r.get("numberOfInjuries") or 0) for r in rows),
        "deaths": sum(int(r.get("numberOfDeaths") or 0) for r in rows),
        "by_component": components.most_common(),
    }
