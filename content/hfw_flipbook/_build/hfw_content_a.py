"""Front matter, M1, M2, M3 - English content from FLIPBOOK HFW (PDF pages)."""
from hfw_dsl import C, H, I, L, T, TB, W, audience, module

# ---------------------------------------------------------------- M1 (+ front matter p1-4)
module("M1", "Introduction to Azithromycin (AZM) Drug Administration",
       "What AZM is, who receives it, how often, and how it is delivered.")
audience("general", evidence="Spec default: purpose, acronyms and M1 are general")
I("m1_p01_01.png", "The AZM medicine bottle, as shown on the cover of the training flipbook.",
  "A white medicine bottle with a teal label reading AZM, inside a white circle.", 1)
H("Purpose of AZM training", 4)
L(["Learn the knowledge and skills to give Azithromycin to eligible children during the campaign.",
   "Understand proper dosing and schedules for AZM, and know when to refer a child to a health facility.",
   "Learn safeguarding practices that protect children and vulnerable people during AZM drug administration.",
   "Learn good interpersonal communication to teach caregivers about AZM and its possible side effects.",
   "Practise every part of AZM drug administration through demonstration and role plays."], 4)
H("Acronyms", 3)
TB(["Acronym", "Meaning"],
   [["ADR", "Adverse Drug Reactions"], ["AZM", "Azithromycin"], ["CU5", "Children under Five Years"],
    ["CDD", "Community Drug Distributors"], ["EOR", "End of Round"], ["FMoH", "Federal Ministry of Health"],
    ["HF", "Health facility"], ["HFW", "Health facility Worker"], ["IDM", "Institute for Disease Modelling"],
    ["LGA", "Local Government Area"], ["LQAS", "Lots Quality Assurance Sampling"], ["MC", "Malaria Consortium"],
    ["NTD", "Neglected Tropical Disease"], ["RBM", "Roll Back Malaria"], ["SAE", "Severe adverse Reaction"],
    ["SMEP", "State Malaria Elimination program"], ["SPHCDA", "State primary health care Development Agency"],
    ["WHO", "World Health organization"]], 3)
I("m1_p05_01.jpg", "In the field — CDDs in AZM vests speak with a family before giving AZM.",
  "Two community drug distributors in yellow AZM vests talk with a seated man and woman holding a child. A baby crawls on a mat. Thatched huts are behind them.", 5)
H("What is AZM?", 7)
T("AZM means Azithromycin.", 7)
T("AZM POS means Azithromycin Powdered Oral Suspension.", 8)
H("AZM benefits", 7)
L(["Azithromycin is a broad-spectrum antibiotic.",
   "It prevents and treats many bacterial infections: acute lower respiratory tract, skin and soft tissue, and gastro-enteric infections.",
   "It also protects against malaria caused by Plasmodium falciparum.",
   "It reduces childhood deaths by preventing and treating pneumonia, diarrhoea and malaria."], 7)
H("Who receives AZM?", 7)
T("AZM drug administration protects children aged 1-59 months from childhood infections.", 7)
T("AZM is given every six months (bi-annually) to children 1 to 59 months of age.", 8, title="How often")
H("How is AZM delivered?", 7)
L(["Trained Community Drug Distributors (CDDs) go door to door.",
   "CDD supervisors, LGA, State and National teams supervise them.",
   "CDDs record AZM administration in the DIGIT HCM app on their devices."], 7)
H("Delivery platforms", 8)
T("AZM MDA uses these child health interventions:", 8)
L(["Neglected tropical disease (NTDs).", "Polio Eradication Initiative campaign.",
   "Seasonal Malaria Chemoprevention.", "Maternal Newborn and Child health (MNCH)."], 8)
T("Using these platforms reduces costs, makes the most of resources and reaches more eligible children.", 8)
H("Tools for each participant", 6)
L(["AZM Job Aid.", "Sample of AZM POS.", "DIGIT HCM App."], 6)

# ---------------------------------------------------------------- M2
module("M2", "Determination of Eligibility for Azithromycin (AZM) Drug Administration",
       "Which children can receive AZM, how to estimate age, who must not receive it, and MUAC assessment.")
audience("general", evidence="Spec default: M2 eligibility is general")
I("m2_p09_01.jpg", "In the field — a CDD shows the AZM pack to a mother and her children.",
  "A woman CDD in an orange headscarf and yellow vest holds out a small AZM box to a seated mother with a baby and a girl in a yellow dress.", 9)
H("Age eligibility", 11)
L(["AZM is given only to healthy children between 1 to 59 months of age.",
   "Children less than one month or older than 59 months are not eligible.",
   "Neonates (less than one month) are not eligible.",
   "A child who is 59 months in round one receives AZM, but is not eligible in the next round."], 11)
H("Why only children 1 to 59 months?", 11)
L(["The AZM safety protocol was set for children 1 month and above.",
   "Younger children are more likely to have side effects.",
   "Children 1 to 59 months have the highest risk of severe malaria and other childhood infections.",
   "This age group has the highest death rates from childhood infections.",
   "Side effects are easier to monitor in this age group (1-59 months)."], 11)
audience("cdd", evidence="Spec default: age determination is cdd")
H("How to find the child's age", 11)
L(["Ask to see the child's health card.", "Ask the caregiver the age of the child.", "Use a calendar of events."], 11)
I("m2_p12_01.png", "Step — use these signs to estimate the age of a child under 12 months.",
  "Four drawings under the label Children 1 to 11 months: a sleeping baby (1 to 2 months), a newborn crossed out in red, a baby held sitting (3 to 4 months), and a crawling baby and a sitting girl (5 to 11 months).", 12)
L(["1 to 2 months: cannot hold head and neck steady when held upright.",
   "Newborn, less than one month: not eligible (marked with a red X).",
   "3 to 4 months: can hold head and neck steady when held upright.",
   "5 to 11 months: can crawl and can sit without help."], 12, title="Children 1 to 11 months")
T("From 3 to 11 months, a child can hold head and neck steady, crawl, and sit without help.", 11)
I("m2_p12_02.png", "Step — a child of 12 to 59 months can stand or walk, but cannot do the two tests marked X.",
  "Drawings under the label Child 12 to 59 months: two children standing and walking, a boy trying to touch his opposite ear over his head with a red X, and a boy standing on one foot with a red X.", 12)
L(["Can stand, walk or run.",
   "CANNOT raise the arm over the head and touch the opposite ear.",
   "CANNOT stand or jump on one foot."], [11, 12], title="Child 12 to 59 months")
W("Older than 59 months: not eligible",
  "A child older than 59 months can raise the arm and touch the opposite ear. They can stand on one leg for 10 secs or jump on one leg. Do not give AZM.", 11)
audience("general", evidence="Spec default: M2 eligibility is general")
H("Eligible and not eligible", 14)
I("m2_p14_01.png", "Do give AZM to healthy children aged 1 to 59 months, like those shown here.",
  "A green tick next to drawings of healthy children: a sleeping baby, a baby held sitting, a crawling baby, a girl eating and a standing boy.", 14)
I("m2_p14_02.png", "Do not give AZM to a child with any of these signs. Refer the child.",
  "A red X next to five line drawings labelled Difficulty in swallowing, Severe acute malnutrition, Not eating and Very Sick. The fifth drawing, a child holding the forehead, has no label.", 14,
  flag="Fifth panel has no label in the PDF; it matches the fever drawing on p16.")
L(["Difficulty in swallowing.", "Severe acute malnutrition.", "Not eating.", "Very sick.",
   "Fifth picture: child holding the forehead (no label in the flipbook)."], 14, title="Not eligible: signs in the picture")
W("Do not give AZM to sick children or children with SAM",
  "Do NOT give AZM to children who are sick or who have Severe Acute Malnutrition (SAM).", 13)
L(["Advise the caregiver to take the child to the nearest health facility for further evaluation.",
   "Complete the referral form and give it to the caregiver to take to the health facility."], 13, title="What to do")
W("Do not hand over medicine or the card",
  "Do not give the caregiver the AZM medicine to give later, or the child record card.", 13)
W("Do not give AZM to children with allergy",
  "Do NOT give AZM to children who are allergic to AZM or other macrolide antibiotics.", 13)
L(["Does the child get sick after taking antibiotic medicines or similar medications?",
   "Has the child taken AZM or similar antibiotics before?",
   "If so, did the child get sick or have reactions such as rashes, swelling or difficulty breathing?"], 13, title="Ask the caregiver")
W("Do not give AZM after recent antibiotics",
  "Do not give AZM after antibiotics or similar medicine taken in the last 28 days (4 weeks).", 15)
L(["Has the child taken any medicine in the last 28 days or 4 weeks?",
   "If yes, what medicine has the child taken in the past one month?",
   "If possible, ask to see the packet to confirm."], 15, title="Ask the caregiver")
H("Severe acute malnutrition: look and feel", 15)
L(["Visible severe wasting: the child looks extremely thin.",
   "The ribs, shoulder blades and bones are very prominent.",
   "The arms and thighs look like \"skin and bones\", with little or no muscle.",
   "The child's buttocks may look flat or baggy."], 15, title="Visible severe wasting")
L(["Press gently with your thumb on the top of both feet for about 3 seconds.",
   "If a pit remains after you remove the thumb, oedema is present.",
   "This shows the child has Kwashiorkor, a form of SAM."], 15, title="Bilateral pitting oedema")
H("AZM should not be given to these children", 15)
L(["Children from 60 months and older.", "Children allergic to AZM or similar antibiotics.",
   "Children who are sick or have fever.", "Children who received AZM or other antibiotics in the last one month.",
   "Children who are currently taking AZM or other antibiotics."], 15)
L(["Children who cannot swallow."], 15)
H("Summary of child eligibility", 16)
I("m2_p16_01.png", "Step — check each row: only a healthy child of 1 to 59 months is eligible.",
  "A chart with Eligible and Refer columns. A green tick for children 1 to 59 months. Red X and refer ticks for a sick child, fever, and allergy or malnutrition. A red X with no referral for AZM in the last 28 days.", 16)
TB(["Situation", "Eligible", "Refer"],
   [["Between 1 to 59 months", "Yes", "No mark"],
    ["When the child is sick", "No", "Yes"],
    ["When the child has fever", "No", "Yes"],
    ["When the child has allergy to antibiotics or similar medicines or has mild/severe/acute malnutrition", "No", "Yes"],
    ["When the child has taken AZM or other similar antibiotics in the last 28 days (4 weeks)", "No", "No mark"]],
   16, title="Summary of child eligibility (transcribed from image)", transcribed=True)
audience("cdd", evidence="Spec default: MUAC measurement is cdd; p17 'Trained CDDs'")
H("MUAC nutrition assessment (children 6–59 months)", 17)
L(["MUAC is done during routine SARMAAN II household visits.",
   "It uses trained CDDs and existing supervision structures.",
   "Data is collected on the Kobo Collect digital platform.",
   "It uses existing household engagement processes.",
   "No extra household visits are needed."], 17)
L(["Measure the Mid-Upper Arm Circumference (MUAC) with a standard colour-coded MUAC tape.",
   "Use the left arm.", "Find the correct midpoint.",
   "Apply the tape lightly or comfortably."], 17, title="How to measure")
W("Do not pull the tape tight", "The MUAC tape must not be tight or too tight.", 17)
T("Kobo Collect classifies MUAC values automatically using WHO/UNICEF thresholds.", 17)
I("m2_p18_01.png", "Step — read the MUAC result and take the action in the same row.",
  "A colour-coded table: green row 12.5 cm or more, yellow row 11.5 to 12.4 cm, pink row less than 11.5 cm, with status, classification and action columns.", 18)
TB(["MUAC Range", "Status", "Classification", "Action Required"],
   [["≥ 12.5 cm", "Well-nourished", "Normal", "No immediate action"],
    ["11.5 - 12.4 cm", "At Risk / MAM", "Moderate Acute Malnutrition", "Immediate referral to health facility for counselling"],
    ["< 11.5 cm", "SAM", "Severe Acute Malnutrition", "Immediate referral to health facility"]],
   18, title="MUAC chart (transcribed from image)", transcribed=True)
I("m2_p19_01.jpg", "Do measure on the left arm, not too tight. Do not use the right arm or pull the tape too tight.",
  "Two illustrated panels. Green panel, Good MUAC assessment: a CDD measures a girl's left arm, labels Left arm and Not too tight. Red panel, Bad MUAC assessment: a CDD measures a child's right arm, labels Right arm and Too tight.", 19)
L(["Good: left arm.", "Good: not too tight.", "Bad: right arm.", "Bad: too tight."], 19,
  title="MUAC right and wrong (transcribed from image)", transcribed=True)
I("m2_p20_01.jpg", "Step — wrap the MUAC tape around the upper arm of a child aged 6-59 months.",
  "Close-up photo of adult hands wrapping a green and red MUAC tape around a child's upper arm. The child wears a striped shirt.", 20)
I("m2_p20_02.png", "The MUAC tape: red from 6 to 11 cm, yellow at 12 cm, green from 13 to 26 cm.",
  "Technical drawing of a MUAC tape with a UNICEF logo, a cm window and a scale from 6 to 26 with red, yellow and green bands. Small dimension labels are not readable.", 20)

# ---------------------------------------------------------------- M3
module("M3", "Steps for Referral of Children to Health Facility",
       "When to refer a child, the referral steps, and how to complete the AZM referral form.")
audience("general", evidence="Spec default: M3 referral basics are general")
I("m3_p21_01.jpg", "In the field — a CDD explains a referral to a caregiver, holding the referral form.",
  "A man in a yellow AZM vest points down the road and holds a paper while talking to a woman carrying a toddler. A second CDD in a vest stands beside her.", 21)
H("When to refer a sick child", 23)
T("A child is sick or has danger signs when the child has:", 23)
L(["Convulsion.", "Fever or high temperature.", "Difficulty breathing.", "Difficulty staying awake.", "Vomiting."], 23)
L(["Not able to eat or drink.", "Severe pains or bleeding.", "Neck pain or severe headache.", "Severe Acute Malnutrition."], 23)
I("m3_p23_01.png", "Do refer the child when the child is sick or has danger signs.",
  "A green tick beside a drawing of a mother holding a sick child, with the labels When the child is sick and When the child has danger signs.", 23)
I("m3_p23_02.png", "Do refer the child when the child has fever.",
  "A green tick beside a drawing of a child holding the forehead, with the label When the child has fever.", 23)
H("Why refer?", 23)
L(["Children with fever may have malaria or other childhood infections.",
   "Malaria, pneumonia and diarrhoea are the leading causes of death in under-five children in Nigeria.",
   "Children with fever need evaluation to avoid complications.",
   "Children with SAM after MUAC screening are excluded, evaluated and given support (resuscitation, feeding programme, etc.)."], 23)
H("Allergy and side effects", 24)
T("Allergies to AZM are rare but may occur.", 24, title="Step 1")
T("Refer a child to the nearest health facility if the child has side effects or suspected adverse reactions.", 24, title="Step 2")
I("m3_p24_01.png", "Do refer a child who shows any of these signs after AZM.",
  "Four drawings labelled Very Sick (mother holding a child), Fever (child holding forehead), Swelling (child with swollen face) and Rash (child with a red rash on the chest).", 24)
I("m3_p24_02.png", "Do not give AZM to a child with any of these signs. Refer the child.",
  "Five line drawings labelled Difficulty in swallowing, Severe acute malnutrition, Not eating, Very Sick and Fever.", 24)
L(["Swelling of the face, mouth, tongue or other parts of the body.", "Nausea or continuous vomiting.",
   "Skin rashes or blistering of the skin.", "Body itching.", "Weakness or fatigue."], 24, title="Possible allergy or reasons for exclusion")
L(["Loss of appetite.", "Abdominal pains, diarrhoea.", "Headache.", "Yellowing of the skin or eyes."], 24)
H("Referral steps", 25)
T("Use these steps for children who are sick, have severe acute malnutrition or have suspected adverse reactions.", 25)
I("m3_p25_01.png", "Step — do not give AZM, fill the referral form, then explain the referral to the caregiver.",
  "Three pictures joined by green arrows: a red X over a photo of suspension poured into a cup (Do Not give AZM), a health worker writing on a form (Fill referral form), and a health worker showing the form to a seated woman (Explain referral to caregiver).", 25)
L(["Do not give AZM.", "Complete the top portion of the referral form.",
   "Explain the reason for the referral and the need to act immediately.",
   "Tell the caregiver how to get to the nearest health facility.",
   "Give the AZM referral form to the caregiver to take to the health facility."], 25)
W("Explain the danger",
  "If the child has fever or SAM, the child could have malaria or other diseases. Explain that the child could get worse or die without immediate treatment.", 25)
T("Explain that the health worker will evaluate the child at the facility.", 25)
audience("cdd", "health_worker", evidence="Form text: 'To be completed by CDD and HFW'; p26 'Show how to complete the top portion of the AZM referral form for the CDDs'", inferred=False)
H("The AZM referral form", 26)
L(["Each CDD team has referral forms with a double carbon copy.",
   "The form tracks the number of children referred to the health facility.",
   "It also tracks the number of children who get to the health facility."], 26)
I("m3_p26_01.png", "Step — the CDD completes the top section; the health facility worker completes the rest.",
  "A one-page form titled AZM Referral Form with partner logos. A black bar reads To be completed by the CDD, followed by boxes, then a second bar reads To be completed by the Health Facility Worker, with numbered yes or no questions.", 26)
L(["Name of child; Beneficiary ID.",
   "Age: 1 11 month: [as printed] or 12- 59 months. Gender: Female or Male.",
   "State, LGA, Ward, Settlement.",
   "Date of referral; Name of health facility referred to.",
   "AZM round (tick): Round 1, 2, 3, 4, 5 or 6."], 26, title="To be completed by the CDD (transcribed from image)", transcribed=True)
L(["Reason for referral: Sick, Fever, or Side effect to AZM.", "State side effect to AZM.",
   "CDD Team Code.", "Signature of Recorder."], 26, title="To be completed by the CDD, continued (transcribed from image)", transcribed=True)
L(["Date of child evaluated; AZM Round: 1 or 2; Name of Health Facility.",
   "Child evaluated to determine cause of illness: YES / NO. Diagnosis.",
   "Child treated: YES / NO. Name of treatment. Dose of treatment.",
   "Child admitted to health facility or referred to hospital for severe illness: YES / NO."], 26,
  title="To be completed by the Health Facility Worker (transcribed from image)", transcribed=True)
L(["Child tested for malaria: YES / NO.", "RDT result: Positive / Negative.",
   "Child admitted to health facility or referred to hospital for severe malaria: YES / NO.",
   "Child with confirmed positive malaria test treated with ACT: YES / NO.", "Name and dose of ACT."], 26,
  title="Child referred with fever (transcribed from image)", transcribed=True)
L(["Child evaluated for adverse drug reaction to AZM: YES / NO.", "National PV form was completed: YES / NO.",
   "NAFDAC E-Reporting Link / Med Safety App was filled: YES / NO.",
   "Child admitted to health facility or referred to hospital for SAE: YES / NO.",
   "Outcome; Name of in-charge; Signature."], 26,
  title="Child with possible adverse drug reaction (transcribed from image)", transcribed=True)
L(["Show how to complete the top portion of the AZM referral form for the CDDs.",
   "Let the CDDs practise filling the top portion of the form.",
   "Role play: a child is 2 years old and has had high fever for 2 days."], 26, title="Demonstrate and practise")
audience("general", evidence="Spec default: key takeaways of M3 referral basics are general")
C("Key take away of module 3",
  "1. Refer children who are sick or malnourished to the nearest health facility. 2. Fill out the referral form and give it to the caregiver to take to the health facility. 3. Explain the reason for referral and encourage the caregiver to take the child to the health facility immediately.", 27)
