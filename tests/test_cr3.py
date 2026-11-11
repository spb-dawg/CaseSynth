import copy
import json
import unittest
from datetime import date
from pathlib import Path

from cr3 import codes, decode, find_flags, render_brief
from cr3.__main__ import main

ROOT = Path(__file__).parent.parent
EXAMPLE = json.loads((ROOT / "examples" / "commercial_rear_end.json").read_text())
AS_OF = date(2026, 11, 11)


def flags_for(report, client_unit=None):
    return find_flags(decode(report), client_unit=client_unit, as_of=AS_OF)


def titles(flags, kind):
    return [f.title for f in flags if f.kind == kind]


class CodeTables(unittest.TestCase):
    def setUp(self):
        self.book = codes.load("2023")

    def test_all_46_code_sheets_loaded(self):
        numbers = sorted(t["code_sheet"] for t in self.book._tables.values())
        self.assertEqual(numbers, list(range(1, 47)))

    def test_contributing_factors_match_official_manual(self):
        # Spot values read directly from CR-100 v29.0, section 4.6.1.2.
        expected = {"20": "Driver Inattention", "22": "Failed to Control Speed",
                    "36": "Failed to Yield ROW – To Pedestrian", "44": "Followed Too Closely",
                    "60": "Unsafe Speed", "61": "Speeding – (Over Limit)", "67": "Intoxicated - Alcohol",
                    "78": "Failed to Slow Down or Move Over for Vehicles Displaying Emergency Lights"}
        for code, meaning in expected.items():
            self.assertEqual(self.book.lookup("contributing_factors", code).meaning, meaning)

    def test_factor_and_defect_tables_are_separate(self):
        self.assertEqual(self.book.lookup("contributing_factors", "14").meaning, "Disabled in Traffic Lane")
        self.assertEqual(self.book.lookup("vehicle_defects", "14").meaning, "Automation Failure")
        self.assertFalse(self.book.lookup("contributing_factors", "10").known)  # 10 is a defect code only
        self.assertEqual(self.book.lookup("vehicle_defects", "10").meaning, "Defective or No Vehicle Brakes")

    def test_codes_missing_from_the_manual_stay_unknown(self):
        for table, code in [("contributing_factors", "72"), ("traffic_control", "1"), ("drug_category", "5")]:
            self.assertFalse(self.book.lookup(table, code).known, (table, code))

    def test_lookup_ignores_case_and_zero_padding(self):
        self.assertEqual(self.book.lookup("contributing_factors", "03").meaning, "Backed without Safety")
        self.assertEqual(self.book.lookup("body_style", "tt").meaning, "Truck Tractor")
        self.assertEqual(self.book.lookup("injury_severity", " k ").meaning, "Fatal Injury")

    def test_wrapped_entries_are_whole(self):
        self.assertEqual(self.book.lookup("sequence_of_events", "19").meaning,
                         "Collision With Work Zone Maintenance Equipment")
        self.assertEqual(self.book.lookup("street_suffix", "EXPY").meaning, "Expressway")
        self.assertEqual(self.book.lookup("fin_resp_type", "1").meaning, "Liability Insurance Policy")


class Decoding(unittest.TestCase):
    def test_unknown_code_is_reported_not_guessed(self):
        report = copy.deepcopy(EXAMPLE)
        report["units"][0]["factors"]["contributing"] = ["72"]
        decoded = decode(report)
        value = decoded.data["units"][0]["factors"]["contributing"][0]
        self.assertEqual((value["meaning"], value["known"]), (None, False))
        self.assertEqual([i.where for i in decoded.issues], ["units[0].factors.contributing[0]"])

    def test_other_form_versions_are_refused(self):
        with self.assertRaises(KeyError):
            decode(EXAMPLE | {"form_version": "2018"})

    def test_damage_rating(self):
        report = copy.deepcopy(EXAMPLE)
        report["units"][0]["damage_ratings"] = ["12-FD-3", "BD-2", "VB-7", "13-FD-9", "banana"]
        decoded = decode(report)
        ratings = decoded.data["units"][0]["damage_ratings"]
        self.assertEqual(ratings[0], {"raw": "12-FD-3", "direction_of_force": "12 o'clock", "area_code": "FD", "severity": 3})
        self.assertIsNone(ratings[1]["direction_of_force"])
        self.assertEqual(ratings[2]["special"], "vehicle catches fire due to the collision")
        self.assertEqual(len([i for i in decoded.issues if "damage_ratings" in i.where]), 3)  # force 13, severity 9, banana

    def test_blank_fields_are_skipped(self):
        report = copy.deepcopy(EXAMPLE)
        report["conditions"]["weather"] = ""
        decoded = decode(report)
        self.assertIsNone(decoded.data["conditions"]["weather"])
        self.assertEqual(decoded.issues, [])


class Flags(unittest.TestCase):
    def test_example_from_the_car_side(self):
        flags = flags_for(EXAMPLE, client_unit=3)
        builders = titles(flags, "builder")
        self.assertIn("Unit 1 (DOE, JOHN Q): contributing factor assigned", builders)
        self.assertIn("Unit 1: commercial vehicle", builders)
        self.assertIn("Unit 1: vehicle defect recorded", builders)
        self.assertIn("Unit 1: charge filed", builders)
        self.assertIn("Unit 1 (DOE, JOHN Q): intrastate-only licence on an interstate trip", builders)
        self.assertIn("Crash in a construction zone", builders)
        self.assertEqual(titles(flags, "dealbreaker"), ["Client unit: ROE, SAM not taken for treatment"])
        self.assertEqual(titles(flags, "verify"), [])

    def test_same_facts_are_dealbreakers_from_the_truck_side(self):
        dealbreakers = titles(flags_for(EXAMPLE, client_unit=1), "dealbreaker")
        self.assertIn("Unit 1 (DOE, JOHN Q): contributing factor assigned", dealbreakers)
        self.assertIn("Unit 1: charge filed", dealbreakers)
        self.assertIn("Client unit: DOE, JOHN Q coded as not injured", dealbreakers)

    def test_without_a_client_unit_fault_is_reported_as_fact(self):
        flags = flags_for(EXAMPLE)
        self.assertEqual(titles(flags, "dealbreaker"), [])
        self.assertIn("Unit 1 (DOE, JOHN Q): contributing factor assigned", titles(flags, "fact"))

    def test_every_flag_names_its_source_field(self):
        for flag in flags_for(EXAMPLE, client_unit=3):
            self.assertTrue(flag.sources, flag.title)

    def test_deadlines_count_from_the_crash_date(self):
        due = {f.title: f.due for f in flags_for(EXAMPLE, client_unit=3) if f.kind == "deadline"}
        self.assertEqual(due["911 audio may be destroyed"], date(2026, 11, 1))
        self.assertEqual(due["Body and dash camera video may be destroyed"], date(2026, 12, 31))
        self.assertEqual(due["Commercial driver's hours-of-service logs may be destroyed"], date(2027, 4, 2))
        self.assertEqual(due["Two-year filing deadline for personal injury"], date(2028, 10, 2))
        passed = [f for f in flags_for(EXAMPLE, client_unit=3) if "PASSED" in f.detail]
        self.assertEqual([f.title for f in passed], ["911 audio may be destroyed"])

    def test_month_end_and_leap_day_deadlines(self):
        report = copy.deepcopy(EXAMPLE)
        report["crash"]["date"] = "02/29/2024"  # MM/DD/YYYY as printed on the form
        due = {f.title: f.due for f in flags_for(report) if f.kind == "deadline"}
        self.assertEqual(due["Two-year filing deadline for personal injury"], date(2026, 2, 28))
        report["crash"]["date"] = "2026-08-31"
        due = {f.title: f.due for f in flags_for(report) if f.kind == "deadline"}
        self.assertEqual(due["Commercial driver's hours-of-service logs may be destroyed"], date(2027, 2, 28))

    def test_unreadable_crash_date_is_flagged_not_guessed(self):
        report = copy.deepcopy(EXAMPLE)
        report["crash"]["date"] = "10-2-26"
        flags = flags_for(report)
        self.assertEqual(titles(flags, "deadline"), [])
        self.assertTrue(any("no crash date" in t for t in titles(flags, "verify")))

    def test_uninsured_other_driver_and_hit_and_run(self):
        report = copy.deepcopy(EXAMPLE)
        report["units"][0]["fin_resp"]["proof"] = "expired"
        self.assertIn("Unit 1 (DOE, JOHN Q): no valid proof of insurance", titles(flags_for(report, 3), "dealbreaker"))
        report["units"][0]["hit_and_run"] = True
        self.assertIn("Unit 1: hit and run", titles(flags_for(report, 3), "dealbreaker"))

    def test_impairment(self):
        report = copy.deepcopy(EXAMPLE)
        driver = report["units"][2]["persons"][0]
        driver.update(alcohol_specimen="2", alcohol_result=0.11)
        self.assertIn("Unit 3: alcohol result 0.11", titles(flags_for(report, 3), "dealbreaker"))
        driver.update(alcohol_specimen="4", alcohol_result=None, drug_result="1", drug_category="8")
        found = titles(flags_for(report, 3), "dealbreaker")
        self.assertIn("Unit 3: alcohol test refused", found)
        self.assertIn("Unit 3: positive drug test", found)

    def test_government_vehicle_adds_notice_deadline(self):
        report = copy.deepcopy(EXAMPLE)
        report["units"][0]["cmv"]["vehicle_operation"] = "4"
        notice = [f for f in flags_for(report, 3) if f.title == "Notice of claim to a governmental unit"]
        self.assertEqual([f.due for f in notice], [date(2027, 4, 2)])
        self.assertEqual([f for f in flags_for(EXAMPLE, 3) if f.title == "Notice of claim to a governmental unit"], [])

    def test_report_consistency_checks(self):
        report = copy.deepcopy(EXAMPLE)
        report["identifiers"].update(total_units=4, total_persons=5, fatal=True)
        report["units"][0]["factors"]["contributing"] = ["22", "60"]
        report["units"][0]["factors"]["may_have_contributed"] = ["22"]
        report["investigator"]["investigation_complete"] = False
        found = titles(flags_for(report, 3), "verify")
        for expected in ["Unit count does not match", "Person count does not match", "Unit 1: speed factors conflict",
                         "Unit 1: factor listed twice", "Investigation not complete",
                         "Fatal box and injury codes disagree"]:
            self.assertIn(expected, found)

    def test_rideshare_keyword_matches_whole_words_only(self):
        report = copy.deepcopy(EXAMPLE)
        report["narrative"] = "Driver HUBER stated he was tired."
        self.assertNotIn("Possible rideshare or delivery driver", [f.title for f in flags_for(report, 3)])
        report["narrative"] = "Driver stated she was logged into Uber with a passenger."
        self.assertIn("Possible rideshare or delivery driver", titles(flags_for(report, 3), "builder"))


class Brief(unittest.TestCase):
    def test_committed_example_brief_is_current(self):
        decoded = decode(EXAMPLE)
        brief = render_brief(decoded, find_flags(decoded, client_unit=3, as_of=AS_OF), client_unit=3)
        self.assertEqual(brief, (ROOT / "examples" / "commercial_rear_end.brief.md").read_text())

    def test_unknown_codes_are_loud_in_the_brief(self):
        report = copy.deepcopy(EXAMPLE)
        report["conditions"]["weather"] = "42"
        decoded = decode(report)
        brief = render_brief(decoded, find_flags(decoded, as_of=AS_OF))
        self.assertIn("**42 = NOT IN OFFICIAL TABLE**", brief)
        self.assertIn("Code not in the official table", brief)

    def test_cli_refuses_unsupported_version(self):
        path = ROOT / "tests" / "_tmp_2018.json"
        path.write_text(json.dumps(EXAMPLE | {"form_version": "2018"}))
        try:
            self.assertEqual(main([str(path)]), 2)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
