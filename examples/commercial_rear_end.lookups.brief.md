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
- **Unit 1: recall matches the recorded vehicle defect.** The officer recorded a vehicle defect, and NHTSA lists 3 recall(s) for the 2019 KENWORTH T680 on the same system: 20V593000 (SERVICE BRAKES, AIR:ANTILOCK); 19V275000 (PARKING BRAKE); 24V145000 (SERVICE BRAKES, AIR:SUPPLY:RESERVOIR/TANK). Preserve the vehicle and confirm this VIN's recall status. _(source: units[0].factors, units[0].vin)_
- **Unit 1: 9 recall(s) for this vehicle line.** NHTSA lists 9 recall(s) for the 2019 KENWORTH T680: ELECTRICAL SYSTEM:WIRING; ELECTRONIC STABILITY CONTROL (ESC); ENGINE AND ENGINE COOLING:ENGINE:DIESEL; EXTERIOR LIGHTING; PARKING BRAKE; POWER TRAIN:CLUTCH ASSEMBLY; SERVICE BRAKES, AIR:ANTILOCK; SERVICE BRAKES, AIR:SUPPLY:RESERVOIR/TANK; STEERING:CRITICAL FASTENERS. These apply to the model line; confirm whether this VIN is affected and repaired. _(source: units[0].vin)_
- **Unit 1: carrier out-of-service rate above the national average.** EXAMPLE FREIGHT LINES LLC, 24 months to 11/09/2026: vehicle 35.0% (national average 22.26%, 21 of 60 inspections); driver 10.2% (national average 6.67%, 9 of 88 inspections). _(source: units[0].cmv.carrier_id_num)_
- **Unit 1: carrier safety rating is Conditional.** FMCSA safety rating Conditional, dated 03/14/2024. _(source: units[0].cmv.carrier_id_num)_
- **Unit 1: carrier federal record.** EXAMPLE FREIGHT LINES LLC (USDOT 0000000): 42 power units, 51 drivers. In the 24 months to 11/09/2026: 88 inspections and 11 reported crashes (1 fatal, 4 injury). Crash counts show involvement, not fault. Source: FMCSA SAFER snapshot page. _(source: units[0].cmv.carrier_id_num)_

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

## Outside records

From NHTSA (vehicles) and FMCSA (carriers), looked up by the VIN and USDOT number on the report. Recalls and complaints are for the make, model and year, not this specific vehicle.

**Unit 1**

- **VIN 1XKEXAMPLE0000001:** 2019 KENWORTH T680, Truck-Tractor, Class 8: 33,001 lb and above (14,969 kg and above)
- **Recall 18V931000** (2018-12-21), POWER TRAIN:CLUTCH ASSEMBLY: PACCAR Incorporated (PACCAR) is recalling certain 2018-2019 Peterbilt 337, 348, 365, 367, 389, 567, 579 and 587 trucks and 2018-2019 Kenworth C500, T270, T370, T440, T660, T680, T800, T880 and W900 trucks equipped with automated manual transmissions.  An internal component in the clutch assembly may fail, possibly resulting in unintended vehicle movement. Consequence: Unintended movement of a vehicle can increase the risk of a crash.
- **Recall 18V657000** (2018-09-21), ENGINE AND ENGINE COOLING:ENGINE:DIESEL: PACCAR Incorporated (PACCAR) is recalling certain 2017-2019 Kenworth C500, T600, T660, T680, T800, T880 and W900 trucks, as well as Peterbilt 367, 386, 389, 567, 579 and 587 trucks, equipped with Cummins ISX15 or X15 diesel engines.  In certain driving conditions, such as on a long down-hill grade, the fuel line may burst if the fuel pump cooling circuit screen becomes restricted. Consequence: If the fuel line bursts, fuel may leak onto the road resulting in a roadway hazard for other motorists.  The engine may also stall without warning, resulting in the vehicle's inability to restart, increasing the risk of a crash.
- **Recall 20V593000** (2020-09-28), SERVICE BRAKES, AIR:ANTILOCK: PACCAR Incorporated (PACCAR) is recalling certain 2016-2021 Kenworth T680 trucks equipped with a 2.1m Cab and WABCO 6S/6M ABS brake system with drum brakes.  The brake systems were manufactured with a standard rear-brake ABS modulator valve instead of a quick release valve, which may exceed the intended service-brake release timing.  As such, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard number 121, "Air Brake Systems." Consequence: Longer than expected service-brake release timing may lengthen vehicle stopping distance, increasing the risk of a crash.
- **Recall 19V275000** (2019-04-05), PARKING BRAKE: PACCAR Incorporated (PACCAR) is recalling certain 2018-2020 T680 and T880 tandem axle vehicles equipped with a parking brake on a single axle and certain models of automated manual transmissions.  During cold temperatures, the signal from the park brake pressure switch to the transmission controller may be delayed possibly resulting in the vehicle moving unexpectedly. Consequence: Unexpected vehicle movement may increase the risk of a crash or injury.
- **Recall 18V816000** (2018-11-16), EXTERIOR LIGHTING: PACCAR Incorporated (PACCAR) is recalling certain 2013-2019 Kenworth T680 and T880 and Peterbilt 579 trucks, greater than 30 feet long and equipped with side extender mounted intermediate marker lamp/turn signals that do not include a reflex reflector.  Since both intermediate side marker lamps and reflex reflectors are required, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard (FMVSS) number 108, "Lamps, Reflective Devices, and Associated Equipment." Consequence: Missing reflex reflectors can reduce the vehicle's visibility to other drivers, increasing the risk of a crash.
- **Recall 21V00N000** (2021-12-29), ELECTRICAL SYSTEM:WIRING: PACCAR Incorporated (PACCAR) is recalling certain 2016-2022 Peterbilt 567, 579, 2021-2022 Peterbilt 536, 2017-2021 Kenworth T880, 2016-2022 Kenworth T680, 2018-2020 Kenworth T440, 2020 Kenworth T270, and 2021 Kenworth T280 vehicles.  The methane detection system will not function if the system loses power. Consequence: The operator may be unaware of a system malfunction or the presence of excessive methane levels, increasing the risk of injury or fire.
- **Recall 20V199000** (2020-04-06), ELECTRONIC STABILITY CONTROL (ESC): PACCAR Incorporated  (PACCAR) is recalling certain 2008-2019 Peterbilt 330, 335, 337, 340, 348, 365, 367, 384, 386, 387, 388, 389, 567, 579 and 587 vehicles and 2008-2020 Kenworth T170, T270, T370, T660, T680, T800, T880, and W900 vehicles equipped with NAMUX Software.  In the event that the Anti-lock Brake System (ABS) loses battery and/or ignition power to the controller, the dash warning light for the ABS may not illuminate to warn the driver of the loss of ABS.  As such, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard (FMVSS) number 121, "Air Brake Systems," and 136, "Electronic Stability Control System on Heavy Vehicles." Consequence: If the driver unknowingly operates the vehicle without the ABS functioning, there would be an increased risk of a crash.
- **Recall 22V277000** (2022-04-25), STEERING:CRITICAL FASTENERS: PACCAR Incorporated (PACCAR) is recalling certain 2018-2020 Kenworth T270, T370, T440, T470, T660, T680, T880, T800, W900, W990; and 2018-2020 Peterbilt 330, 337, 348, 365, 367, 389, 520, 567, and 579 vehicles.  The Dana D-Series axle steer arm fasteners that attach the steering arm to the steering knuckle may fail. Consequence: Fastener failure can result in a loss of steering control, increasing the risk of a crash or injury.
- **Recall 24V145000** (2024-02-24), SERVICE BRAKES, AIR:SUPPLY:RESERVOIR/TANK: PACCAR Incorporated (PACCAR) is recalling certain 2009-2021 Kenworth C500, 2012-2021 Kenworth T440, 2009-2015 Kenworth T660, 2015-2024 Kenworth T680, 2009-2024 Kenworth T800, 2009-2020 Kenworth T370, 2014-2023 Kenworth T880, 2011-2016 Kenworth T470, 2023 Kenworth T480, and 2009-2019 Kenworth W900 vehicles.  The air tanks have an insufficient volume of air for the brake system.  As such, these vehicles fail to comply with the requirements of Federal Motor Vehicle Safety Standard number 121, "Air Brake Systems." Consequence: Insufficient air volume can reduce braking performance and increase the risk of a crash.
- **Carrier:** EXAMPLE FREIGHT LINES LLC (DBA EXAMPLE FREIGHT), USDOT 0000000
- **Address:** 100 EXAMPLE PKWY LAREDO, TX 78040
- **USDOT status:** ACTIVE
- **Operating authority:** AUTHORIZED FOR: Motor Carrier of Property (Except Household Goods) Broker of Household Goods Broker of Property (Except Household Goods) Motor Carrier of Household Goods
- **MC numbers:** MC-000000
- **Fleet:** 42 power units, 51 drivers
- **Safety rating:** Conditional
- **Vehicle inspections, 24 months to 11/09/2026:** 60, 21 out of service (35.0%; national average 22.26%)
- **Driver inspections, 24 months to 11/09/2026:** 88, 9 out of service (10.2%; national average 6.67%)
- **Hazmat inspections, 24 months to 11/09/2026:** 0, 0 out of service (0.0%; national average 4.44%)
- **Reported crashes, same period:** 11 (1 fatal, 4 injury, 6 tow-away). Involvement only, no finding of fault.
- **Carrier record source:** FMCSA SAFER snapshot page.

**Unit 3**

- **VIN 4T1EXAMPLE0000003:** 2021 TOYOTA Camry, Sedan/Saloon, Class 1C: 4,001 - 5,000 lb (1,814 - 2,268 kg)
- **Owner complaints to NHTSA:** 8 filed, 1 involving a crash, 0 a fire, 1 injuries, 0 deaths. Most common: AIR BAGS (2); UNKNOWN OR OTHER (1); POWER TRAIN (1); ENGINE (1); TIRES (1).

## Investigator

- **Name:** OFFICER EXAMPLE
- **ID:** 0000
- **Agency:** SAN ANTONIO POLICE DEPARTMENT
- **Report date:** 2026-10-03
- **Investigation complete:** Yes

---
Codes decoded from: TxDOT CR-100 Instructions to Police for Reporting Crashes, version 29.0 (2025). Deadline rules and legal notes have not been reviewed by an attorney.
