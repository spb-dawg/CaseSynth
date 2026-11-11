"""Command line: python -m cr3 report.json [--client-unit N] [--as-of YYYY-MM-DD] [--lookups] [--json]"""
from __future__ import annotations

import argparse
import json
import sys

from .brief import render_brief
from .decode import decode
from .flags import find_flags, parse_date, sort_flags
from .lookups import enrich, lookup_flags
from .lookups.enrich import fmcsa_webkey_from_env


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cr3", description="Decode a Texas CR-3 crash report record into a brief.")
    ap.add_argument("report", help="path to a structured CR-3 record (JSON); see README.md")
    ap.add_argument("--client-unit", type=int, help="unit number of the firm's client")
    ap.add_argument("--as-of", help="date to count deadlines from (default: today)")
    ap.add_argument("--lookups", action="store_true",
                    help="look up VINs (NHTSA) and USDOT numbers (FMCSA) online; sends only those numbers. "
                         "Set FMCSA_WEBKEY to use FMCSA's keyed API; without it the public SAFER page is read")
    ap.add_argument("--json", action="store_true", help="output decoded data and flags as JSON instead of Markdown")
    args = ap.parse_args(argv)

    with open(args.report, encoding="utf-8") as fh:
        report = json.load(fh)
    try:
        decoded = decode(report)
    except KeyError as exc:
        print(f"Cannot decode: {exc.args[0]}. Only the 2023 CR-3 tables are loaded; "
              "decoding another version with them would give wrong meanings.", file=sys.stderr)
        return 2
    as_of = parse_date(args.as_of) if args.as_of else None
    if args.as_of and as_of is None:
        ap.error("--as-of must be YYYY-MM-DD")
    flags = find_flags(decoded, client_unit=args.client_unit, as_of=as_of)
    lookups = enrich(decoded, fmcsa_webkey=fmcsa_webkey_from_env()) if args.lookups else []
    flags = sort_flags(flags + lookup_flags(decoded, lookups, client_unit=args.client_unit))
    if args.json:
        json.dump({"decoded": decoded.data, "flags": [f.as_dict() for f in flags], "lookups": lookups}, sys.stdout, indent=1)
    else:
        sys.stdout.write(render_brief(decoded, flags, client_unit=args.client_unit, lookups=lookups))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
