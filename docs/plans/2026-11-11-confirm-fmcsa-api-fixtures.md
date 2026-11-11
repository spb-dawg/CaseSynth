# Plan: confirm FMCSA QCMobile API fixtures against live responses

MC session: `session_01PBtJpsSpQFWMNrxjtEtRUt` · started 2026-11-11 · model Fable

## Goal

Close the trust gap left by the session that made the QCMobile API the primary carrier
source (commit 63c3331 on `claude/festive-hopper-ue4t8e`). That session never had a working
`FMCSA_WEBKEY`, so `tests/fixtures/qc_carrier.json`, `qc_dockets.json` and `qc_not_found.json`
were hand-built from FMCSA's published field list, and `parse_api` / `carrier_api` in
`cr3/lookups/fmcsa.py` were written against those assumptions. Only `qc_bad_key.json` is a
real response. This plan has one worker call the live API, reconcile the parser with the real
JSON shape, and replace the hand-built fixtures with trimmed real responses, so every carrier
fact in the brief is sourced from a confirmed shape.

## Owner decisions

- 2026-11-11 First worker (fixture confirmation) approved before this MC session started;
  spawn without asking.
- 2026-11-11 Record shape returned by `parse_api` and `carrier_api` must not change; flags
  and the brief depend on it.
- 2026-11-11 Fixtures keep the fictional carrier EXAMPLE FREIGHT LINES LLC from
  `safer_carrier.html`, with numeric values consistent where tests compare the two sources.

## Tasks

| # | Area | Task | Model (why) | Depends on | Done means |
|---|---|---|---|---|---|
| 1 | lookups | Call the live QCMobile API (2–3 large public carriers, one non-existent USDOT, one docket-numbers call), compare every field `parse_api` reads with the live JSON, fix `parse_api`/`carrier_api` where the shape differs, replace `qc_carrier.json`, `qc_dockets.json`, `qc_not_found.json` with trimmed real responses (fictional carrier substituted), update `tests/fixtures/README.md` with the confirmation date | Opus `claude-opus-5-5`, effort `high`. Touches the lookups parser, three fixtures, the tests and a doc (more than two files); a wrong parse of a safety rating or insurance figure lands in a paralegal's brief. Section 2 puts lookup changes on Opus. Sonnet was considered because the fixture refresh part is bounded, but the parser change cannot be specified in advance of seeing the live JSON. | — | Fixtures are real, confirmed live on 2026-11-11 per the fixtures README; parser matches live shape with return shape unchanged; `python -m unittest discover -s tests` passes (output verbatim in report); live `--lookups` run on the example (fake USDOT) shows the not-found path; no key or `webKey=` URL in any committed file or in the report; pushed to `w/2026-11-11-lookups-confirm-qc-api-fixtures`; no PR |

## Worker roster

| Title | Model / effort | Session ID | Branch | Spawned | Status | Result |
|---|---|---|---|---|---|---|
| W  2026-11-11 lookups · confirm qc api fixtures against live responses | `claude-opus-5-5` / high | `session_01PBtJpuBzVTXVDAHTx8XWr7` | `w/2026-11-11-lookups-confirm-qc-api-fixtures` (platform-assigned outcome branch, same as intended) built on `claude/festive-hopper-ue4t8e` | 2026-11-11 13:36 CST | running | — |

## Log (newest first)

- 2026-11-11 13:37 Plan file created; MC waiting for the worker's `send_message` report (no polling).
- 2026-11-11 13:36 Spawned worker `session_01PBtJpuBzVTXVDAHTx8XWr7` on Opus / high. Prompt
  follows the section 4 template: five numbered steps (live calls saved to scratchpad, field-by-field
  comparison, fixture replacement with fictional substitution, live `--lookups` run on the example,
  unittest plus a `webKey=` grep), with the no-key-in-output constraint repeated explicitly.
- 2026-11-11 13:35 MC session started on `claude/festive-hopper-ue4t8e` (HEAD d4d2f7c). Read
  `docs/MISSION_CONTROL.md`, `README.md`, `docs/plans/TEMPLATE.md`, `tests/fixtures/README.md`,
  and skimmed function and test names in `cr3/lookups/fmcsa.py` and `tests/test_lookups.py`.

## Open questions for the owner

- If the live not-found answer turns out to be an HTTP error rather than 200 with null content,
  `carrier_record` may currently treat it as an API failure and fall back to SAFER (which also
  reports not found). Acceptable, or should the brief distinguish "API says no such carrier" from
  "API unreachable"? The worker is told to report what it finds, not to decide this.
- After this worker lands, the next trust item in the standing priorities is PDF intake, which
  needs real sample CR-3 reports before a parser can be planned. Do you have, or can you obtain,
  redacted sample reports?
