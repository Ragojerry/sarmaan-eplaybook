"""CDD flipbook, PDF pages 28-59: Module 4 with its sections 2 (call-in data), 3 (drug
accountability), 4 (child record card) and cohort tracking."""
from cdd_dsl import TF, C, H, I, L, T, TB, W, fx, module, review

module("CDD-04", 4, "CDD - Module 4: Azithromycin Drug Administration and Recording",
       "Preparing and giving AZM safely, recording on the child record card, house marking, call-in data, drug "
       "accountability and cohort tracking.", 90)

I("cdd_p28_m4_opener.jpg", "Module 4: Azithromycin Drug Administration and Recording.",
  "A mother in a teal hijab gives a boy medicine from a small cup.", 28)
H("Module 4: Azithromycin Drug Administration and Recording", 28)

# p29
L(["AZM POS", "Safe AZM Administration", "Steps to Administering AZM to eligible children", "Completing the AZM Child Record Card",
   "House marking during AZM campaign.", "Accountability, reconciliation and storage"], 29, title="Contents")
L(["AZM Job Aid", "Sample AZM POS"], 29, title="Tools for each participant")

# p30
H("Azithromycin Powdered Oral Suspension (AZM POS)", 30)
L(["The Azithromycin (AZM) comes in small powdered Oral suspension (POS) bottle.",
   "The medicine comes with a small dispensing cup for measuring accurate dose or volume of reconstituted AZM to be administered "
   "to eligible children.",
   "The medicine will need to be reconstituted with 15ml of clean water to obtain 30ml AZM suspension.",
   "Each bottle of AZM will be used to reach 4 children."], 30, title="Explain and show: Azithromycin POS")
I("cdd_p30_reconstitution_steps.png",
  "1. Check expiry date of the medicine. 2. Wash hand. 3. Provide clean water from the household. 4. Reconstitute AZM medicine. "
  "5. Measure out AZM for dispensing.",
  "Five numbered pictures: a medicine bottle marked expiry date, hands washing under a tap, a measuring beaker of water, a CDD "
  "preparing AZM with a mother and child, and AZM suspension poured into a measuring cup.", 30)

# p31
H("Azithromycin drug administration protocol", 31)
L(["The CDD should check the expiry date of drug before reconstitution.",
   "Wash hands with soap and water before administering AZM.",
   "Limit AZM administration to 5 eligible children at a time.",
   "Ask the caregiver to bring drinking water in a small cup."], 31, title="Explain and show: how to safely administer AZM")
L(["First, shake the AZM powder vigorously to loosen it.",
   "Add 15ml of clean water and shake the bottle thoroughly to mix.",
   "For children 1-11 months, determine the dose using the age-based dosing strategy (3-tier dosing schedule) as follows: 1-2 months "
   "will receive 2ml, 3-4 months will receive 3ml while 5-11 months will receive 4ml.",
   "For children 12-59 months: The dosing pole will be used to measure their height (Height based dosing strategy). The measurement "
   "in cm is on one side of the pole while the corresponding dose to be administered to the child is indicated on the opposite side "
   "of the pole.",
   "The DIGIT HCM app will indicate the dose to be administered when the age or height of the child is inputted into the app.",
   "The CDD should measure out the accurate dose of AZM to be administered using the provided dispensing cup.",
   "AZM should be administered to one child per time.",
   "If the child vomits within 5 minutes after receiving AZM, the child should be redosed with the same dose according to their age or height.",
   "Observe the child for 30 minutes after administration for any side effect or Suspected ADR for referral."],
  31, title="Steps for administering AZM")
TF("4.1")  # module quiz 4.1
TF("4.3")  # module quiz 4.3

# p32
I("cdd_p32_dosing_pole_1.jpg", "A CDD measuring the height of a child (within the age group 12-59 months) with a dosing pole.",
  "A CDD in a dark hijab measures a small child standing against a dosing pole while the mother holds the child.", 32)
I("cdd_p32_dosing_pole_2.jpg", "A CDD holding a dosing pole.",
  "A smiling CDD in a purple hijab and green vest stands holding a tall coloured dosing pole.", 32)
I("cdd_p32_measuring_dose.jpg", "A CDD measuring out a dose of AZM.",
  "A CDD in a brown hijab pours AZM suspension into a small measuring cup, with children watching.", 32)

# p33
H("Azithromycin drug administration protocol", 33)
L(["OICs in the facilities will issue AZM medicine and other implementation tools to each CDD team at the beginning of each day of "
   "the implementation period.",
   "CDD teams must meet the OIC every morning during the implementation period to request for AZM medicine needed for "
   "administration to the target population.",
   "Each CDD team is expected to reach a total of 100 children each day during the 4 days distribution period"],
  33, title="How AZM Medicines are issued")
L(["All AZM bottles must be accounted for daily during the MDA.",
   "All used and unused bottles of AZM medicines must be returned to the Health facility OIC.",
   "Partially used AZM medicines remain viable for up to 2 to 3 days and must be reused before a new one is opened.",
   "CDDs must measure the exact dose displayed on the DIGIT app because overdosing or under dosing will result in wastage that will "
   "affect drug reconciliation leading to accountability issues, and drug resistance.",
   "CDD must ensure that dosing poles are returned to the health facility daily.",
   "The OICs must check the technology app to know the number of children reached by each CDD team .",
   "The OICs should document the distribution of AZM in the inventory control cards and all the empty bottles should be properly "
   "arranged in the cartons."], 33, title="What need to be returned to the OICs at the end of each day during MDA")

# p34
H("Correct positioning for administration of AZM", 34)
L(["Ensure that the child is awake.", "Sit the child upright to avoid spitting or vomiting.",
   "Give medicine slowly with the dispensing cup.",
   "Ensure that the child drinks ALL the medicine by rinsing the cup with a small amount of water and give to swallow again",
   "Do not force the child to swallow the medicines by holding the child's head and neck backwards or pinching the nose.",
   "Repeat steps 3,4,5 and 6 until all the children in the group have received AZM.",
   "Redose if the child vomits within 5 minutes of AZM administration.",
   "The CDD team should observe " + fx(34, "ethe", "the") + " child for 30mins for any side effect or suspected adverse reaction."], 34)
review(34, "Step references", "Slide 33 says 'Repeat steps 3,4,5 and 6' but the steps on that slide are not numbered, so it is not "
       "clear which steps are meant. Kept as written.")
L(["Azithromycin POS", "Safe drinking water in a clean cup.", "A calibrated measuring cup."], 34,
  title="STEP 1: Steps for mixing and administering AZM POS. Gather the following required materials")
W("Check the expiry date", "Check the expiry date of the AZM POS before administration. (Do not use if expired).", 34)
L(["Shake the powder to loosen the contents.", "Tap the bottle gently to loosen the dry powder before adding water.",
   "Measure and add 15ml of water to obtain 30ml final volume of AZM suspension.",
   "Use the provided measuring cup to add the correct amount of water.",
   "Close the bottle tightly and shake well for at least 30 secs to ensure that the powder dissolves completely into a smooth suspension.",
   "Shake again before each use to maintain consistency."], 34)
T("The dose of AZM to be administered depends on the child's age: For Children 1-11 months: use age-based dosing Strategy (3-tier "
  "schedule) and for children 12-59months; use height based dosing strategy by measuring their height with a dosing pole.", 34,
  title="Determine and administer the correct dose")

# p35
I("cdd_p35_giving_azm.jpg", "AZM is " + fx(35, "giving", "given") + " slowly and the child properly positioned",
  "A mother in a green hijab holds a baby upright and gives medicine from a small cup.", 35)

# p36
H("Completing the child record card", 36)
L(["The Child's name, age, beneficiary ID, settlement, ward, LGA and Gender.",
   "Indicate the " + fx(36, "doing strategy", "dosing strategy") + " used for the child("
   + fx(36, "age of height-based", "age or height-based") + " dosing strategy).",
   "Tick as appropriate on the age range and indicate the dose of AZM given to the child in ml."],
  36, title="What needs to be recorded on the AZM Child Record Card")
L(["Show CDDs how to complete the card.",
   "Ask the CDDs to complete the child record card for children 1 to 2 months, 3-4 months, 5-11 months and 12-59 months"],
  36, title="Demonstrate and practice")
I("cdd_p36_child_record_card.png",
  "The Child Record Card for drug administration of Azithromycin (AZM) for children aged 1-59 months, to be completed and updated "
  "by CDDs during each round.",
  "The printed child record card: child and household details, the administration record for age-based (1-11 months) and "
  "height-based (12-59 months) dosing, the dosing guideline tables, follow-up on other interventions, a health advisory box and a "
  "detachable part kept at the health facility.", 36)
TB(["Age", "Dosage"], [["1-2 Months", "2 ml"], ["3-4 Months", "3 ml"], ["5-11 Months", "4 ml"]], 36,
   title="Age-Based Dosing Strategy: AZM Administration guideline for children 1-11 months (printed on the card)", transcribed=True)
TB(["Height", "Dosage"], [["50-53 cm", "2 ml"], ["54-64 cm", "4 ml"], ["65-75 cm", "6 ml"], ["76-86 cm", "8 ml"],
                          ["87-97 cm", "10 ml"], ["98-109 cm", "12 ml"], ["110-121 cm", "14 ml"], ["122-129 cm", "16 ml"],
                          ["130-136 cm", "19 ml"], ["137- 140 cm", "25 ml"]], 36,
   title="Height-Based Dosing Strategy: AZM Administration guideline for children 12-59 months (printed on the card)", transcribed=True)
L(["AZM is safe", "All medicines can cause side effects in some children.",
   "If your child becomes sick after AZM administration, take your child immediately to the health facility.",
   "If your child has fever at any time, take the child immediately to the health facility to be tested for malaria",
   "Retain this card for future references during all"], 36, title="Health advice printed on the card")
review(36, "Dosing table on the card (please check)", "The two dosing tables and the health advice are transcribed from the card "
       "picture on slide 35, which is small. Read at high zoom they say: 1-2 months 2 ml, 3-4 months 3 ml, 5-11 months 4 ml; height "
       "50-53 cm 2 ml, 54-64 cm 4 ml, 65-75 cm 6 ml, 76-86 cm 8 ml, 87-97 cm 10 ml, 98-109 cm 12 ml, 110-121 cm 14 ml, 122-129 cm 16 "
       "ml, 130-136 cm 19 ml, 137-140 cm 25 ml. The last two rows break the +2 ml pattern (19 ml, then 25 ml); please confirm "
       "against the dosing pole and the DIGIT HCM app. The last line of the health advice is cut off in the source ('...during all').")

# p37
H("Housemarking guide during AZM MDA", 37)
L(["Marking houses helps CDD supervisors to keep track of the houses visited during implementation so that no child is missed.",
   "Every house visited must be marked with a chalk."], 37, title="Why House Marking is important")
L(["If a child is between 1-59 months and the caregivers is not present to give permission for AZM administration, the CDD should "
   "return during the MDA to visit the house again.",
   "Mark the house to be revisited with the " + fx(37, "later “R”", "letter “R”") + " if it needs to be revisited.",
   "The CDD should re-visit the house and mark it completed."], 37, title="Why it is important to mark houses")
TF("4.2")  # module quiz 4.2
I("cdd_p37_house_marking.jpg", "A CDD marking a house with chalk: AZM/26/1 0041/021/2/2/c.",
  "A CDD in a patterned hijab and yellow vest writes AZM/26/1 and 0041/021/2/2/c in chalk on a house wall.", 37)

# p38
H("Housemarking guide during AZM campaign", 38)
L(["Program: AZM.", "The year given (26 for 2026).", "The round in numbers: 1 or 2 or 3 or 4 or 5 or 6)",
   "The CDD team code (4 digits).", "Number of children eligible for AZM/ number of children given AZM.",
   "Status of the visit: Completed (C). Needs to be revisited (R). Excluded (E): Children not eligible for AZM."],
  38, title="How to mark houses during AZM MDA")
L(["Demonstrate how to mark a house in the year 2026 where: AZM was given to all 3 children in round 3. AZM/26/3/56708/021/3/3/C.",
   "Demonstrate how to mark a house in the year 2026 that will need to be revisited where AZM was given to only 1 child out of the 3 "
   "children in round 3: AZM was given to only 1 child in round 3. AZM/26/3/56708/021/3/1/R.",
   "Demonstrate how to mark a house in the year 2026 where AZM was given to the remaining children in round 3: AZM/26/3/56708/021/3/3/R/C.",
   "Demonstrate how to mark a house in the year 2026 where children are excluded in the round: AZM/26/3/56708/021/0/0/E."],
  38, title="How to mark houses for AZM MDA")
review([37, 38], "House-marking codes", "Slide 37 says the CDD team code has 4 digits, but every example uses '56708/021' (5 digits "
       "plus a further 3-digit group that the format does not explain). The photo on slide 36 shows 'AZM/26/1 0041/021/2/2/c', which "
       "has no round between the year and the team code in the same way. In the photo itself the year '26' is written over the "
       "picture; the underlying photo reads 'AZM/25/1'. Kept as written.")

# p39-p40 call-in data
H("Section 2: Call-in-data reporting during AZM MDA (for CDDs and OICs)", 39)
H("Introduction to call-in data in AZM MDA", 40)
L(["CDD teams should document every child reached according to the two age categories: 1–11 months and 12–59 months.",
   "At the end of each day at the health facility, each CDD team should total the number of children reached in both age categories "
   "(1–11 months and 12–59 months). These totals must correspond with the number of children recorded in the DIGIT HCM app.",
   "The Officer-in-Charge (OIC) should aggregate the totals from all CDD teams in the facility for each age (1–11 months and 12–59 months).",
   "OICs should download the call-in data form from Kobo Collect into their devices for data entry.",
   "Each health facility has a unique Facility ID, which should be used to access the appropriate form.",
   "The aggregated totals for each age category (1–11 months and 12–59 months) should be entered into the Kobo Collect form and submit."],
  40, title="Implementation steps")
L(["CDD teams should document every child reached according to the two age categories: 6 –11 months and 12–59 months.",
   "At the end of each day at the health facility, each CDD team should total the number of children reached in both age categories "
   "(6 –11 months and 12–59 months). These totals must correspond with the number of children recorded in the Kobo Collect tool or DIGIT HCM app.",
   "The Officer-in-Charge (OIC) should aggregate the totals from all CDD teams in the facility for each age (6–11 months and 12–59 months).",
   "OICs should download the call-in data form from Kobo Collect into their devices for data entry.",
   "Each health facility has a unique Facility ID, which should be used to access the appropriate form.",
   "The aggregated totals for each age category (6–11 months and 12–59 months) should be entered into the Kobo Collect form and submit.",
   "Call-in data must be submitted daily throughout the implementation period including mop-up."],
  40, title="For Integrated campaigns (AZM+MUAC; AZM+ MNCHW – VITAMIN A, MUAC, ANC; Albendazole, etc)")
review(40, "Call-in age categories", "For AZM alone the call-in categories are 1-11 and 12-59 months; for integrated campaigns they "
       "are 6-11 and 12-59 months, which leaves children 1-5 months out of the integrated count. Kept as written.")

# p41-p44 drug accountability
I("cdd_p41_reconciliation_photo.jpg", "Section 3: Procedures for Azithromycin drug accountability and reconciliation in the health facility.",
  "Several people bend over open cardboard cartons, sorting white AZM bottles.", 41)
H("Section 3: Procedures for Azithromycin drug accountability and reconciliation in the health facility", 41)
H("Procedures for AZM drug accountability and reconciliation", 42)
L(["OICs should confirm and ensure proper documentation of AZM bottles received in the facility using the Issue and Receipt Voucher "
   "and Inventory Control Card.",
   "OICs are to issue to the CDD teams, the quantities of Azithromycin bottles needed to meet their daily target both physically and "
   "digitally through the technology app. Please note that the quantity of AZM bottles issued digitally in the app must correspond to "
   "the number of physical bottles issued.",
   "All the physical quantities issued to each CDD teams must be documented in the Inventory control card.",
   "CDD teams are to ensure that the physical bottles of AZM are kept safely in the AZM bags provided to avoid unintended losses",
   "In the field, the CDD teams are to ensure that each bottle of AZM POS is reconstituted with exactly 15 ml of water.",
   "During dispensing, CDDs are to ensure that the exact dose displayed on the app is measured using the calibrated cups to avoid over or underdosing.",
   "Any redosing due to vomiting within 5 minutes must be properly captured in the app for accountability.",
   "CDD teams are to ensure that each opened bottle is exhausted before opening another AZM bottle for reconstitution."],
  42, title="Steps for AZM drug accountability (Explain)")
L(["CDD teams should separate the empty AZM bottles from all unopened or unused bottles in the AZM bag.",
   "In the facility, OICs should count the number of empty bottles returned by each CDD team and multiply this by 4 to get the number "
   "of children to be reached. The number is then compared with the number of actual children reached in the DIGIT HCM app.",
   "The number of unopened and empty bottles of AZM returned by each CDD team must correspond to the number of bottles issued to them "
   "in the morning by the OIC.",
   "Both empty and unopened bottles should be arranged in separate cartons in the health facility for ease of accountability.",
   "All missing bottles should be escalated to the LGA logistician and the NTD coordinator for possible investigation.",
   "All AZM bottles (used and unused bottles) should be arranged in cartons and returned to the LGA store within 3 days after "
   "implementation to avoid pilferages and diversion."], 43, title="Steps for AZM drug reconciliation and accountability: continues")
C("Key take away for participants",
  "CDD teams and OICs are responsible for Azithromycin drug accountability at the health facility level. Lack of accountability will "
  "lead to pilferages and diversion that will result in AZM drug influx into the markets and community drug sales outlets. The "
  "reconciliation and accountability of AZM Drugs and other commodities should be conducted daily between the CDD teams and the OICs "
  "in the health facility at the end of the day. All AZM bottles (used and unused bottles) should be arranged in cartons for easy accountability.", 44)

# p45-p53 child record card
H("Section 4: Steps for filling the child record card by CDDs during AZM MDA in SARMAAN II project", 45)
L(["Completing the front page.", "Completing the inner page.", "Age based dosage administration.",
   "Height based dosage administration.", "Tracking of other interventions.", "Completing the detachable sections.",
   "AZM child's information.", "SMC Child information (For Kebbi State- Integrated child record card."], 46, title="Contents")
L(["AZM Job Aid"], 46, title="Tools for each participant")
H("Steps for completing the child record card during AZM MDA", 47)
L(["Why do we need to issue the Child record card.", "Who is supposed to fill the child record card.",
   "What are the contents of the Child record card.", "Why do we need to fill the child record card accurately.",
   "What other interventions are we tracking for every child.",
   "What is the importance of the detachable section of the child record card.",
   "How many years will a Child record card last for each child.",
   "How do we ensure that the caregivers keep the Child Record cards safe for use in subsequent rounds."],
  47, title="Facilitators guide: ask the participants (discuss and explain)")
I("cdd_p47_child_record_card_front.png", "Front page of the Child Record Card for drug administration of Azithromycin (AZM) for children aged 1-59 months.",
  "The front page of the child record card with logos, the child's name, beneficiary ID boxes, date of birth, household details, "
  "gender, CDD team code and phone number, and the detachable child's information.", 47)

L(["Child's Name: Write the Child's name and surname as obtained from the caregiver.",
   "Beneficiary ID: Write the 12-digit alpha-numeric ID generated from the DIGIT app.",
   "Date of birth: Write the date of birth as date/month/year.",
   "Gender: Tick the gender as either male or female.",
   "CDD team code: Write the code of the CDD team that visited the household and administered the medications to the child.",
   "CDD phone number: Write the phone number of the recorder."],
  48, title="Facilitators: explain with practical demonstration. Completing the Front page of the Child Record Card")
L(["Name: Write the name of the caregiver.", "Phone number: Write the contact phone number of the caregiver.",
   "State: Write the State.", "LGA: Write the name of the LGA.", "Ward: Write the name of the Ward.",
   "Settlement: Write the name of the settlement or community"], 48, title="Completing the Household/ Caregivers Information")
T("This record should be completed if the child is between 1 month to 11 months of age.", 48,
  title="Completing the Inner page of the Child Record Card. Age-based dosage administration (1-11 months): administration record")
L(["Year: complete the year of implementation. e.g., 2026.", "Round: Write round:1 or 2 in the year of implementation.",
   "Child's age (months): Write the child's age in months. Note: not more than 11 months.",
   "Dose (ml): Write the dose of Azithromycin administered to the child. Please note that the dose to be administered to the child "
   "will be displayed by the app when the age is inputted into the app.",
   "Date administered: Write the date the AZM was administered to the child :"],
  [48, 50], title="Complete the following elements for a child 1-11 months")
I("cdd_p49_cdd_filling_card.jpg", "A CDD filling the Child Record Card DURING AZM administration",
  "A CDD in a brown hijab writes on a child record card.", 49)
T("This section should be completed when the child is 12 months (1 year) and above.", 50,
  title="Height-based dosage administration (12-59 months): administration record")
L(["Year: complete the year of implementation. e.g. 2026.", "Round: Write the round; 1 or 2 in the year of implementation.",
   "Height (cm): Measure the height of the child using a dosing pole and write the child's height in centimeters.",
   "Dose (ml): Write the dose of Azithromycin administered to the child. Please note that the dose to be administered to the child "
   "will be displayed when the height of the child is entered into the app. This will correspond with the dosage on the opposite side "
   "of the dosing pole",
   "Date administered: Write the date the AZM was administered to the child."], 50,
  title="Complete the following elements for a child 12-59 months")
review([38, 48, 50], "Round numbers", "The child record card records 'round 1 or 2' per year, while the house-marking format allows "
       "rounds '1 or 2 or 3 or 4 or 5 or 6'. Probably rounds per year versus rounds overall; kept as written.")
L(["Last SMC cycle: Yes/No: Tick yes or no if the child received SMC.",
   "Last Polio: Yes/No: Tick yes or no if the child received polio vaccine.",
   "Last Malaria vaccine received: Complete the data on the malaria vaccine received by the child using the immunization card.",
   "Measles/rubella vaccine Yes /No: Tick yes or no if the child received measles or rubella vaccine."], [50, 51],
  title="Tracking other interventions: this section is aimed at tracking other child health interventions received by the child. "
        "This information should be obtained from the caregiver")
T("This section should be accurately completed, detached properly, returned, and kept safely in the health facility.", 51,
  title="Detachable section of the child record card (CRC)")
L(["Beneficiary ID: Write the beneficiary ID of the child as displayed from the app.",
   "Child first name and surname: Write the name and surname of the child which must be the same as the one written above.",
   "Gender: Write the gender of the child as either male or female.", "Age: Write the age of the child.",
   "State: Write the State.", "LGA: Write the name of the LGA.", "Ward: Write the name of the Ward.",
   "Health facility: Write the name of the health facility.", "Settlement: Write the name of the settlement.",
   "CDD Team Code: Write the code of the CDD team that administered medication to the child.",
   "CDD Phone Number: Write the phone number of the recorder."], 51, title="AZM Child information")
H("AZM MDA section of the detachable component of the child record card", 52)
L(["Year: complete the year in the appropriate round (1 or 2)."], 52, title="Age and Height based AZM dosage administration")
L(["Child's age(months): Write the child's age in months.", "Dose (ml): Write the dose of AZM administered to the child.",
   "Date of administration: Write the date that AZM was administered to the child."], 52,
  title="Age-based AZM dosage administration section for children 1-11 months")
L(["Height (cm): Write the height of the child measured in cm.",
   "Dose (ml): Write the dose of AZM administered to the child based on height."], 52,
  title="Height-based AZM dosage administration (12-59 months)")
L(["Child's name: Write the child's name and surname.", "Beneficiary ID: Write the beneficiary ID as displayed in the technology app.",
   "CDD team code: Write the Code of the CDD team that administers SPAQ to the child.", "LGA: Write the name of the LGA.",
   "Ward: Write the name of the Ward.", "Settlement: Write the name of the settlement or community.",
   "Gender: Write the gender of the child either male or female.", "Cycles: indicate the cycle (1-4).",
   "Address: Write the full address of the child or caregiver."], 52, title="SMC child's information (Applicable in Kebbi State)")
T("The Child Record Card is expected to last for 2 years and therefore should be kept safely by the caregivers in the household.", 52,
  title="Safe keeping of the Child record card")
T("Kindly complete this section of the child record card for Seasonal Malaria chemoprevention. The elements are segregated into "
  "year 1 and year 2 categorized into cycles 1 to 4 each.", 53, title="SMC-SPAQ administration - Kebbi State only")
L(["Age: Write the age of the child under this column. Also tick the appropriate age of the child within the box in either age "
   "category: 3 to < 12 months or 12 to 59 months.",
   "Year: Complete the year of implementation.", "Cycle: Tick the cycle of implementation (1 to 4 cycles).",
   "Dates SPAQ was given: Write the date that the SPAQ was administered to the child.",
   "Day 2 AQ: The caregiver should tick this when the second day dose of amodiaquine is administered to the child.",
   "Day 3 AQ: The caregiver should tick this when the third day dose of amodiaquine is administered to the child."], 53,
  title="Complete the elements as follows")
C("Review the health advisory at the back of the card to guide the CDD appropriately.",
  "CDDs should endeavor to leave their phone numbers in the card to enable the caregivers to contact them in case of suspected ADR "
  "for direction on the steps to take as part of Passive ADR monitoring.", 53)

# p54-p59 cohort tracking
H("AZM cohort tracking", 54)
I("cdd_p54_cohort_icon.jpg", "AZM cohort tracking.",
  "An icon of a group of people divided into segments, linked boxes, a magnifying glass over a bar chart and pills, labelled COHORT.", 54)
L(["What is cohort tracking in AZM?", "Why cohort tracking", "Who is responsible for cohort tracking", "How to track cohort"],
  55, title="Contents")
L(["AZM Job Aid"], 55, title="Tools for each participant")
H("Introduction to cohort tracking in AZM", 56)
L(["One of the critical challenges in AZM implementation is ensuring that eligible children are retained throughout the entire campaign period.",
   "Retention tracking becomes paramount to assess the program's effectiveness and ensure consistent protection against malaria.",
   "AZM Cohort Tracking addresses this challenge by systematically monitoring and evaluating the progress of individual children "
   "enrolled in the program across multiple treatment rounds.",
   "Through innovative tools like the DIGIT HCM App, data managers can track the same cohort of beneficiaries over successive rounds, "
   "enabling comprehensive evaluation of the program's impact on preventing key childhood diseases like diarrhea, pneumonia and malaria"], 56)
T("In the context of Safety and Antimicrobial Resistance of Mass Administration of Azithromycin in Children 1–59 months in Nigeria "
  "(SARMAAN II), cohort tracking means following groups of children who receive Azithromycin during each campaign round, so that "
  "their health outcomes can be monitored over time.", 57, title="What is cohort tracking in AZM?")
L(["Measure effectiveness: By tracking cohorts of children who received AZM, researchers and program managers can see how well the "
   "intervention reduces under 5 morbidity and mortality:",
   "Monitor safety: Cohorts help identify any side effects or adverse reactions to the drugs.",
   "Evaluate coverage & adherence: Tracking shows whether children consistently receive all rounds treatment during campaign periods.",
   "Policy decisions: Evidence from cohorts guides governments and partners on whether to expand, adjust, or improve AZM campaigns."],
  57, title="Why Cohort Tracking in AZM Campaigns")
L(["Cohort tracking is not the job of one person; it's a chain of responsibility.", "CDDs gather the raw data,",
   "M&E teams analyze it, and", "policymakers use the insights to improve AZM Campaign.",
   "CDDs administer AZM and record which children received on DIGIT HCM.",
   "Supervisors ensure data is collected correctly and cohorts are defined.",
   "M&E teams analyze cohort data; tracking drop out and provide timely feedback.",
   "Government and IPs uses the findings to adjust campaign strategies."], 58, title="Who are responsible for cohort tracking")
I("cdd_p59_cohort_flow.jpg",
  "Cohort Tracking Responsibility Flow: Community Drug Distributors (administer treatment, collect data) → CDDs supervisors, "
  "health facility supervisors, Nat'l, State & LGA team (monitor & verify data) → State & Country M&E team (analyze & compare "
  "cohorts) → Government & Partners (policy decisions, program adjustments). Data collection (field work) → data reporting "
  "(supervision) → analysis & reports (data analysis) → policy action.",
  "A Malaria Consortium diagram with four coloured boxes from left to right, each with icons, and a row of arrows below: data "
  "collection, data reporting, analysis and reports, policy action.", 59)
TB(["Who", "Role", "Stage"], [
    ["Community Drug Distributors", "Administer Treatment; Collect Data", "Data Collection (Field Work)"],
    ["CDDs Supervisors, Health Facility Supervisors, Nat'l, State & LGA Team", "Monitor & Verify Data", "Data Reporting (Supervision)"],
    ["State & Country M&E Team", "Analyze & Compare Cohorts", "Analysis & Reports (Data Analysis)"],
    ["Government & Partners", "Policy Decisions; Program Adjustments", "Policy Action"],
], 59, title="Cohort Tracking Responsibility Flow", transcribed=True)
