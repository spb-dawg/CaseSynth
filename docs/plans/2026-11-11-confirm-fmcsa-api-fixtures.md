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
| W  2026-11-11 lookups · confirm qc api fixtures against live responses | `claude-opus-5-5` / high | `session_01PBtJpuBzVTXVDAHTx8XWr7` | `w/2026-11-11-lookups-confirm-qc-api-fixtures` (platform-assigned outcome branch, same as intended) built on `claude/festive-hopper-ue4t8e` | 2026-11-11 13:36 CST | done, reviewed, archived | Commit `1abec0b`: 6 files, +133/−28. Live shape confirmed; fixtures real; 62 tests OK. MC recommends merge. |

## Log (newest first)

- 2026-11-11 13:50 MC review (section 5) of `w/2026-11-11-lookups-confirm-qc-api-fixtures` @ `1abec0b`:
  read the full diff, the three fixtures and the worker transcript. Diff is confined to `cr3/lookups/fmcsa.py`
  (`parse_api` only), `tests/test_lookups.py`, the three `qc_*` fixtures and `tests/fixtures/README.md`.
  Record shape unchanged. Transcript shows a test-first sequence (failures, then fixes) ending in
  `Ran 62 tests ... OK`, twice. No key or `webKey=` URL in any committed file; the only `webKey=` hits are the
  pre-existing URL templates and the test's fake key. **Recommendation to owner: ready to merge.**
- 2026-11-11 13:43 Worker reported done. Findings against the hand-built fixtures (every key name matched;
  differences were values and formats): OOS rates arrive unrounded (now rounded to one decimal, half-up, as
  SAFER shows them; checked against live SAFER for 9 rates); `snapshotDate` is always null so `as_of` is the
  retrieval date; `mcs150Outdated` "N" was misread as None (now False); docket list carries `FF` numbers;
  insurance amounts are strings in thousands (parser already right); not-found is HTTP 200 with
  `"content": null` (parser already right). Three tests added, two adjusted, reasons in the test comments.
- 2026-11-11 13:37 Plan file created; MC waiting for the worker's `send_message` report (no polling).
- 2026-11-11 13:36 Spawned worker `session_01PBtJpuBzVTXVDAHTx8XWr7` on Opus / high. Prompt
  follows the section 4 template: five numbered steps (live calls saved to scratchpad, field-by-field
  comparison, fixture replacement with fictional substitution, live `--lookups` run on the example,
  unittest plus a `webKey=` grep), with the no-key-in-output constraint repeated explicitly.
- 2026-11-11 13:35 MC session started on `claude/festive-hopper-ue4t8e` (HEAD d4d2f7c). Read
  `docs/MISSION_CONTROL.md`, `README.md`, `docs/plans/TEMPLATE.md`, `tests/fixtures/README.md`,
  and skimmed function and test names in `cr3/lookups/fmcsa.py` and `tests/test_lookups.py`.

## Findings needing an owner decision (from the worker, 2026-11-11; nothing changed yet)

- **A. Stale national average on the API path.** The API's `*OosRateNationalAverage` figures (20.72 / 5.51 /
  4.5) are labelled `oosRateNationalAverageYear: "2009-2010"`. The SAFER page for the same carriers shows
  22.26 / 6.67 / 4.44 dated 10/30/2026. The brief and the above-average flag print the API figure as if
  current. The record has no field for the year. Options: use SAFER's current averages on the API path;
  carry the year in the text; or accept and note it. Touches flags/brief, so a new Opus worker.
- **B. `as_of` on the API path is the retrieval date**, because `snapshotDate` is always null; SAFER dates the
  same data to its monthly snapshot (11/09/2026). The brief's "24 months to <date>" is off by days.
- **C. `allowedToOperate` is "Y" for INACTIVE carriers** (seen on three live small carriers). The brief and
  flags correctly use `usdot_status`; do not build on `allowed_to_operate`.

## Outside-scope findings (from the worker; candidates for later workers)

- **SAFER fallback parser bug with a reproduction.** Any carrier with an empty DBA name fails
  `parse_snapshot` ("layout was not recognised"): the page text reads `DBA Name: Physical Address:` with one
  space and the regex needs two. Live reproductions: USDOT 53467 (Werner) and 264184 (Schneider). On the
  no-key or API-failure path every such carrier becomes a failed lookup. Bounded bug with a reproduction:
  Sonnet, test first.
- The two sources word the same fields differently (date formats, `entity_type`, `operating_authority`,
  address comma), so the brief's wording changes with the source.
- SAFER lists only MC numbers; the API docket list also has FF numbers.
- Not seen live, so unconfirmed: `oosDate` format, safety ratings "C"/"U", a docket row without a prefix,
  non-404 API error bodies, exact `.x5` rounding ties, BIPD amounts against FMCSA's L&I system.

## Open questions for the owner

- Merge `w/2026-11-11-lookups-confirm-qc-api-fixtures` into `claude/festive-hopper-ue4t8e` (or the main line)?
  MC recommends yes.
- Which of findings A, B, C above should become the next worker, and should the SAFER DBA regex bug be
  bundled into it or run separately on Sonnet?
- After this worker lands, the next trust item in the standing priorities is PDF intake, which
  needs real sample CR-3 reports before a parser can be planned. Do you have, or can you obtain,
  redacted sample reports?
