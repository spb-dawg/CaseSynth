# Saved responses

`vin_*.json`, `recalls_*.json`, `complaints_sample.json`: real NHTSA responses, trimmed.

`safer_*.html`: FMCSA SAFER snapshot pages with a fictional carrier substituted.

`qc_*.json`: FMCSA QCMobile API responses. `qc_bad_key.json` is the real body FMCSA returns
(HTTP 404) for an unknown WebKey. `qc_carrier.json`, `qc_dockets.json` and `qc_not_found.json` are
trimmed real responses, confirmed live on 2026-11-11 (all HTTP 200), with the fictional carrier from
the SAFER page substituted:

- `qc_carrier.json` keeps a live carrier answer's structure, key order, types, date format
  (`YYYY-MM-DD`), unrounded out-of-service rates, `snapshotDate: null` and FMCSA's national averages
  (20.72 / 5.51 / 4.5, labelled `2009-2010`, which differ from the SAFER page's). The carrier's
  identity and facts are EXAMPLE FREIGHT LINES LLC's, with the counts, crashes and rating of
  `safer_carrier.html`; insurance amounts are in thousands of dollars as FMCSA sends them.
- `qc_dockets.json` keeps a live docket-number answer's shape, including an `FF` prefix; the docket
  numbers are fictional (the API sends integers, so SAFER's `MC-000000` placeholder cannot be used).
- `qc_not_found.json` is FMCSA's real answer for a USDOT number with no record, unchanged:
  HTTP 200 with `"content": null`.
