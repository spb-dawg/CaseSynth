# Saved responses

`vin_*.json`, `recalls_*.json`, `complaints_sample.json`: real NHTSA responses, trimmed.

`safer_*.html`: FMCSA SAFER snapshot pages with a fictional carrier substituted.

`qc_*.json`: FMCSA QCMobile API responses. `qc_bad_key.json` is the real body FMCSA returns
(HTTP 404) for an unknown WebKey. `qc_carrier.json`, `qc_dockets.json` and `qc_not_found.json`
were written by hand from the API's published field list with the same fictional carrier as the
SAFER page, because no key was available when they were made. Confirm them against a live
response (`python -m cr3 ... --lookups` with `FMCSA_WEBKEY` set) the first time one is.
