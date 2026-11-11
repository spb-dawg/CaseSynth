# Crash report brief: EXAMPLE-0001

Texas CR-3, form version 2023. Client: Unit 3. Every item below is a fact read from the report with the field it came from. Contributing factors are the officer's opinion. Verify against the report before relying on anything here.

## Possible dealbreakers

- **Client unit: ROE, SAM not taken for treatment.** ROE, SAM is coded injured but no transport is recorded. Expect the insurer to argue a gap in treatment. _(source: disposition)_

## Case builders

- **Unit 1 (DOE, JOHN Q): contributing factor assigned.** Officer's opinion that this unit contributed to the crash: 22 = Failed to Control Speed; 20 = Driver Inattention. Listed in priority order. _(source: units[0].factors.contributing)_
- **Unit 1 (DOE, JOHN Q): possible contributing factor.** Officer recorded as may have contributed: 40 = Fatigued or Asleep. _(source: units[0].factors.may_have_contributed)_
- **Unit 1: vehicle defect recorded.** Officer recorded: 10 = Defective or No Vehicle Brakes. Possible claim against the owner, a maintenance provider or the manufacturer. Check recalls for 2019 KENWORTH T680 (VIN 1XKEXAMPLE0000001) and preserve the vehicle. _(source: units[0].factors)_
- **Unit 1 (DOE, JOHN Q): licence restrictions.** Restrictions on the licence: K = Intrastate only. Check whether the driver was complying. _(source: units[0].driver_license.restrictions)_
- **Unit 1: owner is not the driver.** Driven by DOE, JOHN Q, owned or leased by EXAMPLE FREIGHT LINES LLC. Possible employer liability or negligent entrustment, and a second insurance policy. _(source: units[0].owner_lessee.name)_
- **Unit 1: commercial vehicle.** EXAMPLE FREIGHT LINES LLC, ID 1 = US DOT 0000000; operation 1 = Interstate Commerce; type 9 = Tractor/Semi Trailer; GVWR 80000. Pull the carrier's federal safety and insurance records and send a preservation letter (driver file, logs, onboard data, dashcam, post-crash drug and alcohol tests). _(source: units[0].cmv)_
- **Unit 1 (DOE, JOHN Q): intrastate-only licence on an interstate trip.** Licence restriction K = Intrastate only, but the vehicle operation is coded 1 = Interstate Commerce. _(source: units[0].driver_license.restrictions, units[0].cmv.vehicle_operation)_
- **Unit 3: A = Suspected Serious Injury.** ROE, JANE A is coded A = Suspected Serious Injury. _(source: units[2].persons[0].injury_severity)_
- **Unit 1: charge filed.** FAILED TO CONTROL SPEED (citation EX123456). _(source: charges[0])_
- **Crash in a construction zone.** Construction zone marked. Identify the contractor and the traffic control plan. _(source: crash.road.construction_zone)_
- **Narrative mentions evidence to secure.** Keyword match: dash cam, video, witness. The CR-3 has no witness section, so witnesses and video appear only in the narrative. _(source: narrative)_

## Deadlines

- **911 audio may be destroyed.** 2026-11-01 (PASSED 10 days ago as of 2026-11-11). State minimum retention for 911 recordings is 30 days (local retention schedule PS). Send a preservation and open-records request. _(source: crash.date)_
- **Body and dash camera video may be destroyed.** 2026-12-31 (50 days left as of 2026-11-11). State minimum retention is 90 days; San Antonio PD keeps crash video 180 days (Procedure 410). An open-records request extends retention. _(source: crash.date)_
- **Commercial driver's hours-of-service logs may be destroyed.** 2027-04-02 (142 days left as of 2026-11-11). Carriers must keep records of duty status for six months (49 CFR 395.8). Send a preservation letter to the carrier. _(source: crash.date)_
- **Two-year filing deadline for personal injury.** 2028-10-02 (691 days left as of 2026-11-11). Tex. Civ. Prac. & Rem. Code 16.003. Exceptions and tolling apply. _(source: crash.date)_

## Crash

- **Date and time:** 2026-10-02 at 1742
- **Location:** San Antonio, Bexar County
- **Road:** IH = Interstate 35
- **Roadway part:** 1 = Main/Proper Lane
- **Speed limit:** 65
- **Intersecting road:** LR = Local Road/Street (Street, Rd., Ave., Blvd., Pl., Trl., Beach, Alley, Boat Ramp), EXAMPLE RD
- **Fatal:** No
- **Commercial vehicle:** Yes
- **School bus:** No
- **Active school zone:** No

## Conditions

- **Weather:** 1 = Clear
- **Light:** 1 = Daylight
- **Surface:** 1 = Dry
- **Traffic control:** 17 = Marked Lanes
- **Roadway type:** 3 = Two-Way, Divided, Protected Median
- **Alignment:** 1 = Straight, Level
- **Entering roads:** 97 = Not Applicable

## Unit 1

- **Unit type:** 1 = Motor Vehicle
- **Vehicle:** 2019 KENWORTH T680
- **Body style:** TT = Truck Tractor
- **Colour:** WHI = White
- **VIN:** 1XKEXAMPLE0000001
- **Plate:** TX EX4MPL1
- **Parked:** No
- **Hit and run:** No
- **Licence:** 2 = Commercial Driver Lic.; class A = Class A; state TX
- **Endorsements:** N = Tank Vehicles
- **Restrictions:** A = With corrective lenses; K = Intrastate only
- **Owner or lessee:** EXAMPLE FREIGHT LINES LLC (owner)
- **Proof of insurance:** YES
- **Insurance type:** 1 = Liability Insurance Policy
- **Insurer:** EXAMPLE COMMERCIAL INSURANCE CO
- **Policy number:** EX-CA-000111
- **Damage ratings:** 12-FD-3 (force from 12 o'clock, area code FD, severity 3 of 7)
- **Contributing factors:** 22 = Failed to Control Speed; 20 = Driver Inattention
- **May have contributed:** 40 = Fatigued or Asleep
- **Vehicle defects, may have contributed:** 10 = Defective or No Vehicle Brakes

**Commercial vehicle section**

- **Carrier:** EXAMPLE FREIGHT LINES LLC
- **Carrier address:** 100 EXAMPLE PKWY, LAREDO, TX
- **Carrier ID:** 1 = US DOT: 0000000
- **Operation:** 1 = Interstate Commerce
- **Vehicle type:** 9 = Tractor/Semi Trailer
- **Cargo body:** 3 = Van/Enclosed Box
- **GVWR:** 80000
- **Disabling damage:** No
- **Hazmat released:** No
- **Sequence of events:** 13 = Collision Involving Motor Vehicle in Transport
- **Trailers:** unit 2: 2 = Semi-Trailer

**Person 1: DOE, JOHN Q**

- **Role:** 1 = Driver
- **Seat:** 1 = Front Left
- **Age:** 47
- **Injury severity:** N = Not Injured
- **Ejected:** 1 = No
- **Restraint:** 1 = Shoulder and Lap Belt
- **Airbag:** 1 = Not Deployed
- **Helmet:** 97 = Not Applicable
- **Alcohol specimen:** 96 = None
- **Drug specimen:** 96 = None
- **Drug result:** 97 = Not Applicable
- **Drug category:** 97 = Not Applicable
- **Solicitation:** N = No Solicit

## Unit 2

- **Unit type:** 6 = Towed/Pushed/Trailer
- **Vehicle:** 2017 UTILITY
- **Body style:** TL = Trailer, Semi-Trailer, or Pole Trailer
- **Plate:** TX EXTRL01
- **Parked:** No
- **Hit and run:** No
- **Owner or lessee:** EXAMPLE FREIGHT LINES LLC (owner)

## Unit 3 (client)

- **Unit type:** 1 = Motor Vehicle
- **Vehicle:** 2021 TOYOTA CAMRY
- **Body style:** P4 = Passenger Car, 4-Door
- **Colour:** SIL = Silver
- **VIN:** 4T1EXAMPLE0000003
- **Plate:** TX EX4MPL3
- **Parked:** No
- **Hit and run:** No
- **Licence:** 1 = Driver License; class C = Class C; state TX
- **Endorsements:** 96 = None
- **Restrictions:** 96 = None
- **Owner or lessee:** ROE, JANE A (owner)
- **Proof of insurance:** YES
- **Insurance type:** 1 = Liability Insurance Policy
- **Insurer:** EXAMPLE MUTUAL
- **Policy number:** EX-PA-000333
- **Damage ratings:** 6-BD-5 (force from 6 o'clock, area code BD, severity 5 of 7)
- **Towed to:** EXAMPLE TOWING

**Person 1: ROE, JANE A**

- **Role:** 1 = Driver
- **Seat:** 1 = Front Left
- **Age:** 34
- **Injury severity:** A = Suspected Serious Injury
- **Ejected:** 1 = No
- **Restraint:** 1 = Shoulder and Lap Belt
- **Airbag:** 5 = Deployed, Multiple
- **Helmet:** 97 = Not Applicable
- **Alcohol specimen:** 96 = None
- **Drug specimen:** 96 = None
- **Drug result:** 97 = Not Applicable
- **Drug category:** 97 = Not Applicable
- **Solicitation:** N = No Solicit

**Person 2: ROE, SAM**

- **Role:** 2 = Passenger/Occupant
- **Seat:** 3 = Front Right
- **Age:** 9
- **Injury severity:** C = Possible Injury
- **Ejected:** 1 = No
- **Restraint:** 7 = Child Booster Seat
- **Airbag:** 1 = Not Deployed
- **Helmet:** 97 = Not Applicable
- **Alcohol specimen:** 96 = None
- **Drug specimen:** 96 = None
- **Drug result:** 97 = Not Applicable
- **Drug category:** 97 = Not Applicable
- **Solicitation:** N = No Solicit

## Charges

- Unit 1, person 1: FAILED TO CONTROL SPEED (citation EX123456)

## Injured taken to

- Unit 3, person 1: EXAMPLE UNIVERSITY HOSPITAL by SAFD EMS

## Officer's narrative

> Unit 3 was stopped in traffic in the construction zone. Unit 1 towing Unit 2 failed to control speed and struck Unit 3 from behind. Driver of Unit 1 stated he had been driving since early morning. A witness in a following vehicle provided dash cam video.

## Investigator

- **Name:** OFFICER EXAMPLE
- **ID:** 0000
- **Agency:** SAN ANTONIO POLICE DEPARTMENT
- **Report date:** 2026-10-03
- **Investigation complete:** Yes

---
Codes decoded from: TxDOT CR-100 Instructions to Police for Reporting Crashes, version 29.0 (2025). Deadline rules and legal notes have not been reviewed by an attorney.
