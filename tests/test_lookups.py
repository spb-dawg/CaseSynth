import copy
import json
import unittest
from datetime import date
from pathlib import Path

from cr3 import decode, find_flags, render_brief
from cr3.flags import sort_flags
from cr3.lookups import enrich, fmcsa, lookup_flags, nhtsa
from cr3.lookups.http import HttpError, LookupFailed

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
EXAMPLE = json.loads((ROOT / "examples" / "commercial_rear_end.json").read_text())
AS_OF = date(2026, 11, 11)


def fixture(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def fake_fetch(vin="vin_clean.json", carrier="safer_carrier.html", api="qc_carrier.json", fail=()):
    """Stand in for the network: answer each service from a saved response.

    `api="bad_key"` answers the FMCSA API the way the real service does for an unknown WebKey.
    """
    calls = []

    def fetch(url):
        calls.append(url)
        truck = "1XK" in url or "KENWORTH" in url.upper()
        if "mobile.fmcsa" in url and api == "bad_key":
            raise HttpError("mobile.fmcsa.dot.gov", 404, fixture("qc_bad_key.json"))
        for marker, name in (("DecodeVinValues", vin if truck else "vin_camry.json"),
                             ("recallsByVehicle", "recalls_kenworth_t680_2019.json" if truck else None),
                             ("complaintsByVehicle", None if truck else "complaints_sample.json"),
                             ("docket-numbers", "qc_dockets.json"),
                             ("mobile.fmcsa", api),
                             ("safer.fmcsa", carrier)):
            if marker in url:
                if marker in fail:
                    raise LookupFailed(f"{marker}: timed out")
                return fixture(name) if name else '{"count": 0, "results": []}'
        raise AssertionError(f"unexpected URL {url}")

    fetch.calls = calls
    return fetch


KEY = "test-web-key-not-real"


def run(report=EXAMPLE, client_unit=3, webkey=None, **kw):
    decoded = decode(report)
    lookups = enrich(decoded, fetch=fake_fetch(**kw), fmcsa_webkey=webkey)
    return decoded, lookups, lookup_flags(decoded, lookups, client_unit=client_unit)


def titles(flags, kind=None):
    return [f.title for f in flags if kind in (None, f.kind)]


class Carrier(unittest.TestCase):
    def test_snapshot_fields(self):
        c = fmcsa.carrier_snapshot("USDOT 1234567", fake_fetch())
        self.assertEqual((c["legal_name"], c["dba_name"], c["usdot"]), ("EXAMPLE FREIGHT LINES LLC", "EXAMPLE FREIGHT", "1234567"))
        self.assertEqual((c["usdot_status"], c["out_of_service_date"]), ("ACTIVE", None))
        self.assertEqual((c["power_units"], c["drivers"], c["total_inspections"]), (42, 51, 88))
        self.assertEqual(c["inspections"]["vehicle"],
                         {"count": 60, "out_of_service": 21, "oos_rate": 35.0, "national_oos_rate": 22.26})
        self.assertEqual(c["crashes"], {"fatal": 1, "injury": 4, "tow": 6, "total": 11})
        self.assertEqual(c["safety_rating"], "Conditional")

    def test_unknown_number_returns_none(self):
        self.assertIsNone(fmcsa.carrier_snapshot("9999999", fake_fetch(carrier="safer_not_found.html")))

    def test_changed_page_layout_fails_loudly(self):
        with self.assertRaises(LookupFailed):
            fmcsa.parse_snapshot("<html><body>Company Snapshot redesigned</body></html>")

    def test_non_numeric_id_is_rejected_before_any_request(self):
        fetch = fake_fetch()
        with self.assertRaises(LookupFailed):
            fmcsa.carrier_snapshot("NONE", fetch)
        self.assertEqual(fetch.calls, [])


class CarrierApi(unittest.TestCase):
    """FMCSA's keyed QCMobile API, primary when a WebKey is given."""

    def test_api_record_matches_the_snapshot_shape(self):
        api = fmcsa.carrier_api("USDOT 1234567", fake_fetch(), KEY)
        page = fmcsa.carrier_snapshot("USDOT 1234567", fake_fetch())
        self.assertEqual(set(api) - {"mcs150_outdated"}, set(page))
        for field in ("legal_name", "dba_name", "usdot", "usdot_status", "out_of_service_date", "power_units",
                      "drivers", "crashes", "safety_rating"):
            self.assertEqual(api[field], page[field], field)
        self.assertEqual(api["inspections"]["vehicle"], page["inspections"]["vehicle"])
        self.assertEqual(api["source"], fmcsa.SOURCE_API)
        self.assertEqual(page["source"], fmcsa.SOURCE_SAFER)

    def test_api_only_fields(self):
        c = fmcsa.carrier_api("1234567", fake_fetch(), KEY)
        self.assertEqual(c["mc_numbers"], ["MC-123456", "MC-654321"])
        self.assertEqual(c["operating_authority"], "AUTHORIZED (common carrier, broker)")
        self.assertEqual(c["rating_date"], "2024-03-14")
        self.assertEqual(c["as_of"], "2026-11-09")
        self.assertIsNone(c["total_inspections"])
        self.assertEqual(c["insurance"], {"bipd_required": True, "bipd_required_amount": 750000, "bipd_on_file": 750000,
                                          "cargo_on_file": 0, "bond_on_file": 0})
        self.assertTrue(c["allowed_to_operate"])

    def test_authority_wording(self):
        text = lambda **kw: fmcsa._authority_text({f"{k}AuthorityStatus": v for k, v in kw.items()})
        self.assertEqual(text(common="N", contract="N", broker="N"), "NOT AUTHORIZED (no authority on file)")
        self.assertEqual(text(common="I", contract="N", broker="N"), "NOT AUTHORIZED (authority inactive)")
        self.assertEqual(text(common="N", contract="A", broker="N"), "AUTHORIZED (contract carrier)")
        self.assertTrue(text(common="N", contract="N", broker="N").startswith("NOT AUTHORIZED"))  # what the flag checks

    def test_unknown_number_returns_none(self):
        self.assertIsNone(fmcsa.carrier_api("9999999", fake_fetch(api="qc_not_found.json"), KEY))

    def test_bad_key_fails_loudly_without_revealing_it(self):
        with self.assertRaises(LookupFailed) as cm:
            fmcsa.carrier_api("1234567", fake_fetch(api="bad_key"), KEY)
        self.assertIn("rejected the WebKey", str(cm.exception))
        self.assertNotIn(KEY, str(cm.exception))

    def test_unrecognised_json_fails_loudly(self):
        with self.assertRaises(LookupFailed):
            fmcsa.parse_api('{"content": {"somethingElse": 1}}')
        with self.assertRaises(LookupFailed):
            fmcsa.parse_api("<html>maintenance</html>")

    def test_docket_lookup_failure_does_not_sink_the_record(self):
        c = fmcsa.carrier_api("1234567", fake_fetch(fail=("docket-numbers",)), KEY)
        self.assertEqual(c["mc_numbers"], [])
        self.assertEqual(c["legal_name"], "EXAMPLE FREIGHT LINES LLC")

    def test_key_is_sent_only_to_the_api_host(self):
        fetch = fake_fetch()
        fmcsa.carrier_record("1234567", fetch, webkey=KEY)
        for url in fetch.calls:
            self.assertIn("mobile.fmcsa.dot.gov", url)
            self.assertIn(f"webKey={KEY}", url)

    def test_no_key_means_safer_page_only(self):
        fetch = fake_fetch()
        record, note = fmcsa.carrier_record("1234567", fetch)
        self.assertEqual(record["source"], fmcsa.SOURCE_SAFER)
        self.assertIsNone(note)
        self.assertTrue(all("safer.fmcsa" in url for url in fetch.calls))

    def test_api_failure_falls_back_to_the_page_with_a_note(self):
        for kw in ({"api": "bad_key"}, {"fail": ("mobile.fmcsa",)}):
            fetch = fake_fetch(**kw)
            record, note = fmcsa.carrier_record("1234567", fetch, webkey=KEY)
            self.assertEqual(record["source"], fmcsa.SOURCE_SAFER)
            self.assertIn("used the SAFER snapshot page instead", note)
            self.assertNotIn(KEY, note)
            self.assertTrue(any("safer.fmcsa" in url for url in fetch.calls))

    def test_both_sources_failing_is_a_failed_lookup(self):
        with self.assertRaises(LookupFailed):
            fmcsa.carrier_record("1234567", fake_fetch(fail=("mobile.fmcsa", "safer.fmcsa")), webkey=KEY)


class Vehicle(unittest.TestCase):
    def test_clean_vin(self):
        v = nhtsa.decode_vin(" 1xkexample0000001 ", fake_fetch())
        self.assertEqual((v["vin"], v["make"], v["model"], v["year"], v["clean"]),
                         ("1XKEXAMPLE0000001", "KENWORTH", "T680", 2019, True))

    def test_bad_vin_keeps_the_warning(self):
        v = nhtsa.decode_vin("1XKEXAMPLE0000001", fake_fetch(vin="vin_bad.json"))
        self.assertFalse(v["clean"])
        self.assertIn("Check Digit", v["error_text"])

    def test_recalls_and_complaints(self):
        recalls = nhtsa.recalls("KENWORTH", "T680", 2019, fake_fetch())
        self.assertEqual(len(recalls), 9)
        self.assertIn("SERVICE BRAKES, AIR:ANTILOCK", [r["component"] for r in recalls])
        self.assertEqual(recalls[0]["received"], "2018-12-21")  # NHTSA sends 21/12/2018
        summary = nhtsa.complaints("TOYOTA", "CAMRY", 2021, fake_fetch())
        self.assertEqual(summary["total"], 8)
        self.assertEqual(sum(count for _, count in summary["by_component"]) >= 8, True)

    def test_make_and_model_are_url_encoded(self):
        fetch = fake_fetch()
        nhtsa.recalls("KENWORTH", "T 680 & CO", 2020, fetch)
        self.assertIn("model=T%20680%20%26%20CO", fetch.calls[0])


class Enrichment(unittest.TestCase):
    def test_only_vin_and_usdot_number_are_sent(self):
        fetch = fake_fetch()
        enrich(decode(EXAMPLE), fetch=fetch)
        sent = " ".join(fetch.calls).upper()
        for private in ("DOE", "ROE", "EX-CA-000111", "EX4MPL1", "LAREDO"):
            self.assertNotIn(private, sent)
        self.assertIn("1XKEXAMPLE0000001", sent)
        self.assertIn("QUERY_STRING=0000000", sent)

    def test_units_without_vin_or_usdot_are_skipped(self):
        _, lookups, _ = run()
        self.assertEqual([r["unit_num"] for r in lookups], [1, 3])  # unit 2 is the trailer, no VIN recorded

    def test_carrier_flags(self):
        _, _, flags = run()
        found = titles(flags, "builder")
        self.assertIn("Unit 1: carrier out-of-service rate above the national average", found)
        self.assertIn("Unit 1: carrier safety rating is Conditional", found)
        self.assertIn("Unit 1: carrier federal record", found)
        rate = next(f for f in flags if "out-of-service rate" in f.title)
        self.assertIn("vehicle 35.0% (national average 22.26%, 21 of 60 inspections)", rate.detail)
        self.assertNotIn("hazmat", rate.detail)  # no hazmat inspections, so no rate to compare

    def test_recall_matching_the_officers_defect_code(self):
        _, _, flags = run()
        match = next(f for f in flags if f.title == "Unit 1: recall matches the recorded vehicle defect")
        self.assertIn("SERVICE BRAKES, AIR:ANTILOCK", match.detail)  # officer coded 10 = brakes
        self.assertNotIn("CLUTCH", match.detail)
        report = copy.deepcopy(EXAMPLE)
        report["units"][0]["factors"]["defects_may_have_contributed"] = []
        _, _, flags = run(report)
        self.assertNotIn("Unit 1: recall matches the recorded vehicle defect", titles(flags))
        self.assertIn("Unit 1: 9 recall(s) for this vehicle line", titles(flags, "builder"))

    def test_carrier_name_mismatch(self):
        report = copy.deepcopy(EXAMPLE)
        report["units"][0]["cmv"]["carrier_name"] = "SOME OTHER TRUCKING INC"
        _, _, flags = run(report)
        self.assertIn("Unit 1: carrier name does not match the USDOT number", titles(flags, "verify"))
        _, _, flags = run()
        self.assertNotIn("Unit 1: carrier name does not match the USDOT number", titles(flags))

    def test_usdot_number_not_found(self):
        _, lookups, flags = run(carrier="safer_not_found.html")
        self.assertIsNone(lookups[0]["carrier"])
        self.assertIn("Unit 1: USDOT number not found", titles(flags, "verify"))

    def test_bad_vin_uses_the_reports_vehicle_not_the_decode(self):
        _, lookups, flags = run(vin="vin_bad.json")
        self.assertEqual(lookups[0]["vehicle"], {"make": "KENWORTH", "model": "T680", "year": 2019})
        self.assertIn("Unit 1: VIN did not decode cleanly", titles(flags, "verify"))
        self.assertNotIn("Unit 1: vehicle does not match its VIN", titles(flags))

    def test_clean_vin_that_disagrees_with_the_report(self):
        report = copy.deepcopy(EXAMPLE)
        report["units"][0].update(veh_make="FREIGHTLINER", veh_year=2016)
        _, _, flags = run(report)
        mismatch = next(f for f in flags if f.title == "Unit 1: vehicle does not match its VIN")
        self.assertIn("make is FREIGHTLINER on the report but KENWORTH from the VIN", mismatch.detail)
        self.assertIn("year is 2016 on the report but 2019 from the VIN", mismatch.detail)

    def test_failed_lookup_is_flagged_and_the_rest_still_runs(self):
        _, lookups, flags = run(fail=("DecodeVinValues",))
        self.assertIn("Unit 1: outside lookup did not complete", titles(flags, "verify"))
        self.assertEqual(lookups[0]["carrier"]["legal_name"], "EXAMPLE FREIGHT LINES LLC")
        _, lookups, flags = run(fail=("safer.fmcsa",))
        self.assertNotIn("carrier", lookups[0])
        self.assertEqual(len(lookups[0]["recalls"]), 9)

    def test_api_record_drives_the_same_flags(self):
        _, lookups, flags = run(webkey=KEY)
        c = lookups[0]["carrier"]
        self.assertEqual(c["source"], fmcsa.SOURCE_API)
        self.assertNotIn("carrier_note", lookups[0])
        found = titles(flags, "builder")
        self.assertIn("Unit 1: carrier out-of-service rate above the national average", found)
        self.assertIn("Unit 1: carrier safety rating is Conditional", found)
        record = next(f for f in flags if f.title == "Unit 1: carrier federal record")
        self.assertIn("60 vehicle inspections, 88 driver inspections", record.detail)
        self.assertIn("Liability insurance on file: $750,000", record.detail)
        self.assertIn(fmcsa.SOURCE_API, record.detail)
        self.assertNotIn("Unit 1: carrier's liability insurance on file is below the required amount", found)

    def test_underinsured_carrier_is_flagged(self):
        fetch = fake_fetch()
        low = json.loads(fixture("qc_carrier.json"))
        low["content"]["carrier"]["bipdInsuranceOnFile"] = "0"
        decoded = decode(EXAMPLE)
        lookups = enrich(decoded, fetch=lambda url: json.dumps(low) if "carriers/0000000?" in url else fetch(url), fmcsa_webkey=KEY)
        flags = lookup_flags(decoded, lookups, client_unit=3)
        under = next(f for f in flags if "liability insurance" in f.title)
        self.assertIn("requires $750,000", under.detail)
        self.assertIn("$0 on file", under.detail)

    def test_fallback_is_noted_in_the_lookup_record_not_as_an_error(self):
        _, lookups, flags = run(webkey=KEY, api="bad_key")
        self.assertEqual(lookups[0]["carrier"]["source"], fmcsa.SOURCE_SAFER)
        self.assertIn("rejected the WebKey", lookups[0]["carrier_note"])
        self.assertEqual(lookups[0]["errors"], [])
        self.assertNotIn("Unit 1: outside lookup did not complete", titles(flags))

    def test_key_never_reaches_the_output(self):
        decoded, lookups, extra = run(webkey=KEY, api="bad_key")
        flags = sort_flags(find_flags(decoded, client_unit=3, as_of=AS_OF) + extra)
        brief = render_brief(decoded, flags, client_unit=3, lookups=lookups)
        self.assertNotIn(KEY, brief)
        self.assertNotIn(KEY, json.dumps(lookups))
        self.assertIn("used the SAFER snapshot page instead", brief)

    def test_carrier_findings_are_not_raised_against_the_client(self):
        _, _, flags = run(client_unit=1)
        self.assertEqual([t for t in titles(flags) if "carrier" in t], [])

    def test_committed_example_brief_with_lookups_is_current(self):
        decoded, lookups, extra = run()
        flags = sort_flags(find_flags(decoded, client_unit=3, as_of=AS_OF) + extra)
        brief = render_brief(decoded, flags, client_unit=3, lookups=lookups)
        path = ROOT / "examples" / "commercial_rear_end.lookups.brief.md"
        self.assertEqual(brief, path.read_text())


if __name__ == "__main__":
    unittest.main()
