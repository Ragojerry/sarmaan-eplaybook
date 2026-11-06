"""M4 - English content from FLIPBOOK HFW (PDF pages 28-60)."""
from hfw_dsl import C, H, I, L, T, TB, W, audience, module

module("M4", "Azithromycin Drug Administration and Recording",
       "Preparing and giving AZM, recording on the Child Record Card, house marking, call-in data, drug accountability and cohort tracking.")
audience("general", evidence="Spec default: M4 administration protocol is general")
I("m4_p28_01.jpg", "Step — the caregiver gives AZM slowly from the dispensing cup while the child sits upright.",
  "Photo of a woman in a teal headscarf holding a small plastic cup to the lips of a young boy sitting on her lap.", 28)
H("AZM Powdered Oral Suspension (AZM POS)", 30)
L(["AZM comes in a small bottle of powdered oral suspension (POS).",
   "It comes with a small dispensing cup to measure an accurate dose.",
   "Reconstitute it with 15ml of clean water to obtain 30ml AZM suspension.",
   "Each bottle of AZM is used to reach 4 children."], 30)
I("m4_p30_01.png", "Step — check expiry, wash hands, get clean water, reconstitute, then measure the dose.",
  "Five numbered pictures in a row: 1 a bottle labelled Expiry Date, 2 hands washed under a tap, 3 a measuring jug of water, 4 a CDD in a vest holding a bottle with a family, 5 white suspension poured into a cup.", 30)
L(["Check the expiry date of the medicine.", "Wash hands.", "Provide clean water from the household.",
   "Reconstitute AZM medicine.", "Measure out AZM for dispensing."], 30, title="Steps in the picture (transcribed from image)", transcribed=True)
H("Safe AZM administration", 31)
L(["Check the expiry date of the drug before reconstitution.",
   "Wash hands with soap and water before giving AZM.",
   "Limit AZM administration to 5 eligible children at a time.",
   "Ask the caregiver to bring drinking water in a small cup."], 31)
W("Do not use expired AZM", "Check the expiry date of the AZM POS before administration. Do not use it if it has expired.", 33)
H("Mixing AZM POS", [31, 33])
L(["Azithromycin POS.", "Safe drinking water in a clean cup.", "A calibrated measuring cup."], 33, title="Gather the materials")
L(["Shake or tap the bottle to loosen the dry powder.",
   "Measure and add 15ml of water to obtain 30ml final volume of AZM suspension.",
   "Use the provided measuring cup to add the correct amount of water.",
   "Close the bottle tightly and shake well for at least 30 secs, until the powder fully dissolves.",
   "Shake again before each use."], [31, 33], title="Mix")
H("Dose by age and height", 31)
TB(["Age", "Dose"], [["1-2 months", "2ml"], ["3-4 months", "3ml"], ["5-11 months", "4ml"]], 31,
   title="Children 1-11 months: age-based dosing (3-tier schedule)")
L(["For children 12-59 months, measure height with the dosing pole (height-based dosing).",
   "The pole shows height in cm on one side and the matching dose on the other side.",
   "The DIGIT HCM app shows the dose when you enter the child's age or height.",
   "Measure the exact dose with the provided dispensing cup."], 31)
H("Giving AZM", [31, 33])
L(["Ensure the child is awake.", "Sit the child upright to avoid spitting or vomiting.",
   "Give the medicine slowly with the dispensing cup.",
   "Rinse the cup with a little water and give it, so the child drinks ALL the medicine.",
   "Give AZM to one child at a time."], [31, 33])
W("Do not force the child",
  "Do not force the child to swallow by holding the head and neck backwards or pinching the nose.", 33)
L(["If the child vomits within 5 minutes, redose with the same dose for the age or height.",
   "Observe the child for 30 minutes after administration for any side effect or suspected ADR.",
   "Refer any child with a side effect or suspected ADR."], [31, 33], title="After giving AZM")
H("How AZM is issued and returned", 32)
L(["OICs in the facilities issue AZM and other tools to each CDD team at the start of each day.",
   "CDD teams meet the OIC every morning to request the AZM they need.",
   "Each CDD team should reach a total of 100 children each day, over the 4 days distribution period."], 32)
L(["All AZM bottles must be accounted for daily during the MDA.",
   "All used and unused bottles must be returned to the health facility OIC.",
   "Partially used AZM stays viable for up to 2 to 3 days. Use it before opening a new bottle.",
   "CDDs must return the dosing poles to the health facility daily."], 32, title="Returned to the OIC at the end of each day")
W("Measure the exact dose",
  "Measure the exact dose shown in the DIGIT app. Overdosing or underdosing wastes drug, causes accountability issues and drug resistance.", 32)
L(["The OIC checks the technology app for the number of children reached by each CDD team.",
   "The OIC documents AZM distribution in the inventory control cards.",
   "All empty bottles are arranged in the cartons."], 32, title="OIC checks")
audience("cdd", evidence="Spec default: Child Record Card is cdd; p34 'Show CDDs how to complete the card'")
H("The AZM Child Record Card", 34)
L(["Record the child's name, age, beneficiary ID, settlement, ward, LGA and gender.",
   "Indicate the dosing strategy used: age-based or height-based.",
   "Tick the age range and write the dose of AZM given, in ml."], 34)
I("m4_p34_01.png", "Step — fill the card at each round and write the dose given in ml.",
  "A Child Record Card with partner logos, child details, an administration record grid, an age-based dosing table, a height-based dosing table, a safety message box, and a detachable strip below a dashed line.", 34)
L(["Child's Name; Beneficiary ID; State; LGA; Ward; Settlement.",
   "Gender: Male or Female; Age.", "CDD Team Code; CDD Phone No.",
   "Name of Household Head; Phone."], 34, title="Child details (transcribed from image)", transcribed=True)
TB(["Year", "Round"], [["Year 1 (202_)", "Round 1"], ["Year 1 (202_)", "Round 2"], ["Year 2 (202_)", "Round 1"], ["Year 2 (202_)", "Round 2"]],
   34, title="Administration record (transcribed from image)", transcribed=True)
T("Age-based dosage (1-11 Months): Child's Age (Months), Dose (ml), Date Administered. Height-Based Dosage (12-59 Months): Height in CM, Dose (ml), Date Administered.", 34,
  title="Administration record columns (transcribed from image)")
TB(["Age", "Dosage"], [["1-2 Months", "2 ml"], ["3-4 Months", "3 ml"], ["5-11 Months", "4 ml"]], 34,
   title="Age-based dosing strategy, children 1-11 months (transcribed from image)", transcribed=True)
TB(["Height", "Dosage"],
   [["50-53 cm", "2 ml"], ["54-64 cm", "4 ml"], ["65-75 cm", "6 ml"], ["76-86 cm", "8 ml"], ["87-97 cm", "10 ml"],
    ["98-109 cm", "12 ml"], ["110-121 cm", "14 ml"], ["122-129 cm", "16 ml"], ["130-136 cm", "19 ml"], ["137- 140 cm", "25 ml"]],
   34, title="Height-based dosing strategy, children 12-59 months (transcribed from image)", transcribed=True)
TB(["Intervention", "Last received"],
   [["SMC: Yes/No", "Last SMC Received: _/_/202_"], ["Malaria vaccine: Yes/No", "Last Malaria Vaccine Received: _/_/202.."],
    ["Measles/Rubella: Yes/No", "Last Measles/Rubella vaccine received: _/_/202.."]],
   34, title="Follow up on uptake of other interventions (transcribed from image)", transcribed=True)
L(["AZM is safe.", "All medicines can cause side effects in some children.",
   "If your child becomes sick after AZM administration, take your child immediately to the health facility.",
   "If your child has fever at any time, take the child immediately to the health facility to be tested for malaria.",
   "Retain this card for future references during all [text cut off on the card]."], 34,
  title="Message on the card (transcribed from image)", transcribed=True)
T("Detachable strip, to be detached and kept at the health facility: Height/Age-based AZM dosage administration (12-59 Months). Columns: Year, Round, Height in CM / Age in Months, Dose (ml), Date Administered.", 34,
  title="Detachable strip (transcribed from image)")
L(["Show CDDs how to complete the card.",
   "Ask CDDs to complete the card for children 1 to 2 months, 3-4 months, 5-11 months and 12-59 months."], 34, title="Demonstrate and practise")
audience("cdd", "supervisor_monitor", evidence="p35 'Marking houses helps CDD supervisors to keep track of the houses visited'; spec default: house marking is cdd")
H("House marking", 35)
L(["Marking houses helps CDD supervisors track the houses visited, so no child is missed.",
   "Every house visited must be marked with chalk.",
   "If a child of 1-59 months is home but no caregiver can give permission, return during the MDA.",
   "Mark a house that needs a revisit with the letter \"R\".",
   "Revisit the house and mark it completed."], 35)
I("m4_p35_01.jpg", "Step — write the house mark in chalk on the wall after the visit.",
  "Photo of a woman in a patterned headscarf and yellow vest writing on a wall in chalk: AZM/25/1 with a 6 written over the 5, and 0041/021/2/2/c below.", 35,
  flag="Code in the photo (AZM/25/1, 6 overlaid; 0041/021/2/2/c) differs from the p36 format and examples.")
L(["Program: AZM.", "The year given (26 for 2026).", "The round in numbers: 1 or 2 or 3 or 4 or 5 or 6.",
   "The CDD team code (4 digits).", "Number of children eligible for AZM / number of children given AZM."], 36, title="What the house mark shows")
L(["Completed (C).", "Needs to be revisited (R).", "Excluded (E): children not eligible for AZM."], 36, title="Status of the visit")
TB(["Situation (2026, round 3)", "House mark"],
   [["AZM given to all 3 children", "AZM/26/3/56708/021/3/3/C"],
    ["AZM given to only 1 child out of 3; revisit needed", "AZM/26/3/56708/021/3/1/R"],
    ["AZM given to the remaining children on the revisit", "AZM/26/3/56708/021/3/3/R/C"],
    ["Children excluded", "AZM/26/3/56708/021/0/0/E"]], 36, title="House mark examples")
audience("cdd", "health_worker", evidence="p37 'Call-in-data Reporting during AZM MDA (For CDDs and OICs)'", inferred=False)
H("Call-in data reporting", [37, 40])
T("Call-in data are daily reports that OICs submit during MDA rounds. They give real-time updates on CDD deployment, drug availability and coverage.", 40)
I("m4_p39_01.jpg", "In training — health workers learn how to submit call-in data.",
  "Photo of a woman facilitator in a SARMAAN II shirt beside a flipchart, teaching health workers in green uniforms seated at tables in a training room.", 39)
L(["What is call-in data?", "Who submits call-in data?", "How often is call-in data submitted?",
   "What are the sources of call-in data?", "How do we ensure the call-in data in the facility is accurate?"], 39, title="Facilitator: ask the participants")
L(["Enables rapid decision-making.", "Helps identify high-risk LGAs/HFs early.", "Supports drug redistribution planning.",
   "Monitors CDDs' presence and performance.", "Strengthens overall MDA quality."], 40, title="Why call-in data is important")
L(["Number of CDDs deployed vs active CDDs.", "Settlements covered.", "Drug stocks (balance, shortages and expiries).",
   "Daily children treated.", "Challenges reported by field teams."], 40, title="Key components of call-in data")
L(["CDD teams record every child reached in two age groups: 1–11 months and 12–59 months.",
   "At the end of each day, each team totals the children reached in both age groups.",
   "These totals must match the number of children recorded in the DIGIT HCM app.",
   "The OIC adds up the totals from all CDD teams in the facility for each age group.",
   "Call-in data must be submitted daily throughout the implementation, including mop-up."], 42, title="Implementation steps")
L(["OICs download the call-in data form from Kobo Collect onto their devices.",
   "Each health facility has a unique Facility ID to open the right form.",
   "OICs enter the totals for each age group in the Kobo Collect form and submit."], 42, title="Submitting on Kobo Collect")
L(["Age groups are 6–11 months and 12–59 months.",
   "Totals must match the Kobo Collect tool or the DIGIT HCM app.",
   "The OIC aggregates and submits on Kobo Collect in the same way."], 42,
  title="Integrated campaigns (AZM+MUAC; AZM+ MNCHW – Vitamin A, MUAC, ANC; Albendazole, etc)")
audience("supervisor_monitor", "other", evidence="p40 roles: 'CDDs Supervisors: Validate', 'LGA M&E', 'State Team', 'National and State M&E'", inferred=False)
TB(["Who", "Role"],
   [["CDDs", "Provide daily treatment figures."],
    ["CDD Supervisors", "Validate reports submitted by CDDs and compare with DIGIT HCM figures."],
    ["OICs", "Consolidate, clean and report call-in data daily."],
    ["LGA M&E", "Ensure accuracy and timely submission of data by OICs."],
    ["State Team", "Ensure that each LGA submits its data on time."],
    ["National and State M&E", "Analyze and provide feedback daily."]], 40, title="Roles and responsibilities")
L(["CDD absenteeism.", "Drug shortages.", "Low coverage in hard-to-reach areas.",
   "Incorrect reporting formats.", "Missing HFs or settlements."], 40, title="Common issues detected via call-in data")
L(["Coverage monitoring.", "Identifying hotspots.", "Daily coordination meetings.",
   "Mid-course correction decisions.", "Reporting to donors and national programs."], 41, title="How call-in data is used")
I("m4_p41_01.jpg", "Step — check call-in figures against DIGIT HCM records before submitting.",
  "Photo of a health worker in blue scrubs and a head wrap reading a phone at a desk with open registers. Clinic posters are on the wall.", 41)
L(["Use a standardized template for reporting.", "Supervisors verify the data daily.",
   "Submit daily call-in data on time.", "Cross-check with DIGIT HCM records for accuracy.",
   "Use the dashboard and the number of bottles used for triangulation."], 41, title="Improving call-in data quality")
audience("health_worker", "logistician", "cdd", evidence="p44 'OICs should confirm...'; p44 'CDD teams are to ensure...'; p45 'escalated to the LGA logistician'; spec default: accountability and reconciliation is logistician", inferred=False)
H("Drug accountability and reconciliation in the health facility", 43)
I("m4_p43_01.jpg", "Step — count and arrange AZM bottles in cartons for accountability.",
  "Photo of several people bending over open cardboard cartons, taking out and sorting white AZM bottles.", 43)
L(["OICs document AZM bottles received using the Issue and Receipt Voucher and the Inventory Control Card.",
   "OICs issue the bottles each CDD team needs for its daily target, physically and in the technology app.",
   "The number of bottles issued in the app must match the physical bottles issued.",
   "All physical quantities issued to each CDD team are documented in the Inventory Control Card."], 44, title="OIC steps")
L(["Keep AZM bottles safely in the AZM bags provided, to avoid losses.",
   "Reconstitute each bottle with exactly 15 ml of water.",
   "Measure the exact dose shown on the app with the calibrated cups.",
   "Capture any redosing for vomiting within 5 minutes in the app.",
   "Finish each opened bottle before opening another."], 44, title="CDD team steps")
L(["CDD teams separate empty bottles from unopened or unused bottles in the AZM bag.",
   "The OIC counts each team's empty bottles and multiplies by 4. This gives the number of children to be reached.",
   "The OIC compares this number with the children reached in the DIGIT HCM app.",
   "Unopened plus empty bottles returned must equal the bottles issued that morning."], 45, title="End of day reconciliation")
L(["Arrange empty and unopened bottles in separate cartons in the health facility.",
   "Escalate all missing bottles to the LGA logistician and the NTD coordinator for investigation.",
   "Return all AZM bottles (used and unused) in cartons to the LGA store within 3 days after implementation."], 45, title="Storage and returns")
C("Key take away: drug accountability",
  "CDD teams and OICs are responsible for AZM accountability at the health facility. Lack of accountability leads to pilferage and diversion of drugs into markets and drug sales outlets. Reconcile AZM and other commodities daily, at the end of the day. Arrange all used and unused bottles in cartons.", 46)
audience("cdd", evidence="p47 'STEPS FOR FILLING THE CHILD RECORD CARD BY CDDs'", inferred=False)
H("Steps for completing the Child Record Card", 47)
L(["Why do we issue the Child Record Card?", "Who fills the card?", "What does the card contain?",
   "Why must the card be filled accurately?", "How many years does a card last for each child?"], 49, title="Facilitator: discuss with participants")
I("m4_p49_01.png", "Step — use the front page of the card for the child's and household's details.",
  "Front page of a Child Record Card with partner logos and a stray [Picture] label. Fields for child's name, beneficiary ID boxes, date of birth, household name and phone, gender, CDD team code, a Child's information block and the heading Age-based AZM dosage administration (1-11 Months).", 49,
  flag="Second version of the card (differs from p34); low-resolution source.")
L(["Child's Name; Beneficiary ID (boxes).", "Date of Birth (DD/MM/YY); Age.",
   "Name; Phone No.; State; LGA; Ward; Settlement.", "Gender: Female, Male; CDD Team Code; CDD Phone No.",
   "Child's information: Child Name; Beneficiary ID; State; LGA; Ward; Settlement; CD D Team Code; CDD Phone No."], 49,
  title="Front page fields, second card version (transcribed from image; one line hidden by a cut line)", transcribed=True)
L(["Child's name: the child's name and surname from the caregiver.",
   "Beneficiary ID: the 12-digit alpha-numeric ID generated by the DIGIT app.",
   "Date of birth: date/month/year.", "Gender: tick male or female.",
   "CDD team code and CDD phone number: the team that visited, and the recorder's phone."], 50, title="Front page")
L(["Name and phone number of the caregiver.", "State, LGA, Ward.", "Settlement or community."], 50, title="Household / caregiver information")
L(["Complete this record if the child is 1 month to 11 months old.",
   "Year: the year of implementation, e.g. 2026.", "Round: 1 or 2 in the year of implementation.",
   "Child's age (months): not more than 11 months.",
   "Dose (ml) and date administered. The app shows the dose when you enter the age."], [50, 51], title="Inner page: age-based dosage (1-11 months)")
L(["Complete this record when the child is 12 months (1 year) and above.",
   "Year and round (1 or 2), as above.", "Height (cm): measure with the dosing pole and write it in centimetres.",
   "Dose (ml): the app shows it when you enter the height; it matches the dosing pole.",
   "Date administered."], 51, title="Inner page: height-based dosage (12-59 months)")
L(["Ask the caregiver about other child health interventions.", "Last SMC cycle: tick yes or no.",
   "Last Polio: tick yes or no.", "Last malaria vaccine received: use the immunization card.",
   "Measles/rubella vaccine: tick yes or no."], [51, 52], title="Tracking other interventions")
L(["Complete the detachable section accurately, detach it properly, return it and keep it safely in the health facility.",
   "AZM child information: beneficiary ID from the app; first name and surname as above; gender; age.",
   "State, LGA, Ward, Health facility, Settlement.", "CDD team code and CDD phone number.",
   "Age-based (1-11 months): year, round, age, dose, date. Height-based (12-59 months): height (cm), dose."], [52, 53], title="Detachable section")
L(["Child's name and Beneficiary ID from the technology app.", "CDD team code of the team that gives SPAQ.",
   "LGA, Ward, Settlement, Gender, Address.", "Cycles: 1 to 4 in year 1 and year 2.",
   "Age: tick 3 to < 12 months or 12 to 59 months."], [53, 54], title="SMC child information (Kebbi State integrated card)")
L(["Dates SPAQ was given.", "Day 2 AQ: the caregiver ticks when the second day dose of amodiaquine is given.",
   "Day 3 AQ: the caregiver ticks when the third day dose of amodiaquine is given."], 54, title="SMC-SPAQ administration (Kebbi State)")
C("Keep the card safe",
  "The Child Record Card is expected to last for 2 years. Caregivers should keep it safely in the household.", 53)
T("Review the health advisory on the back of the card. CDDs should leave their phone numbers on the card. Caregivers can then call them about a suspected ADR (passive ADR monitoring).", 54)
audience("supervisor_monitor", "other", evidence="Spec default: cohort tracking is supervisor_monitor and other; p59 'M&E teams analyze it', 'Government and IPs uses the findings'")
H("Cohort tracking", 55)
I("m4_p55_01.jpg", "Cohort tracking follows the same groups of children over time.",
  "Line-art icon: a circle split into groups of people, linked boxes, a magnifier over a bar chart and capsules, with the word COHORT below.", 55)
T("In SARMAAN II, cohort tracking follows groups of children who receive AZM in each round. Their health outcomes are monitored over time.", 58)
L(["Keeping eligible children in the programme for the whole campaign is a key challenge.",
   "Retention tracking shows the programme's effectiveness.",
   "Cohort tracking monitors each enrolled child across many treatment rounds.",
   "The DIGIT HCM app lets data managers track the same children over successive rounds."], 57)
L(["Measure effectiveness: see how well AZM reduces under-5 illness and death.",
   "Monitor safety: find side effects or adverse reactions.",
   "Evaluate coverage and adherence: check children receive every round.",
   "Policy decisions: guide governments and partners to expand, adjust or improve AZM campaigns."], 58, title="Why cohort tracking")
L(["CDDs give AZM and record the children treated in DIGIT HCM.",
   "Supervisors ensure data is collected correctly and cohorts are defined.",
   "M&E teams analyse cohort data, track drop-out and give timely feedback.",
   "Government and IPs use the findings to adjust campaign strategies."], 59, title="Who is responsible")
I("m4_p60_01.jpg", "Step — data moves from CDDs to supervisors, to M&E teams, to government and partners.",
  "Infographic titled Cohort Tracking Responsibility Flow with the Malaria Consortium logo. Four coloured boxes with icons linked by arrows, and four arrows below: Data Collection, Data Reporting, Analysis and Reports, Policy Action.", 60)
L(["Community Drug Distributors: administer treatment; collect data (field work).",
   "CDD Supervisors, Health Facility Supervisors, Nat'l, State and LGA Team: monitor and verify data (supervision).",
   "State and Country M&E Team: analyze and compare cohorts (data analysis).",
   "Government and Partners: policy decisions; program adjustments (policy action)."], 60,
  title="Cohort tracking responsibility flow (transcribed from image)", transcribed=True)
