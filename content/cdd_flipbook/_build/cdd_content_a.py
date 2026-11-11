"""CDD flipbook, PDF pages 1-27: front matter and Modules 1-3. Wording as in the PDF;
spelling fixes go through fx() and questions through review()."""
from cdd_dsl import TF, C, H, I, L, T, TB, W, fx, module, review

# ---------------------------------------------------------------- Module 1 (+ front matter)
module("CDD-01", 1, "CDD - Module 1: Introduction to Azithromycin (AZM) Drug Administration",
       "About this training flipbook, then what AZM is, who receives it, how often, and how it is delivered.", 20)

# p1 cover
I("cdd_p01_cover.png",
  "Cover of the Azithromycin Drug Administration Training Flipbook for Community Drug Distributors (CDDs).",
  "Flipbook cover: Federal Ministry of Health and NPHCDA logos, the title Azithromycin Drug Administration "
  "Training Flipbook, an AZM medicine bottle, and the Malaria Consortium, SARMAAN-II Project and Gates Foundation logos.", 1)
H("Azithromycin Drug Administration Training Flipbook", 1)
T("SARMAAN || Training Document. Community Drug Distributors (CDDs).", 1)

# p2 contents
H("Contents", 2)
TB(["Section", "Page"], [
    ["Purpose of AZM Training", "3"],
    ["Module 1 Introduction to Azithromycin Drug Administration", "4"],
    ["Module 2 Determination of eligibility for Azithromycin AZM Drug Administration", "8"],
    ["Module 3 Steps for referral of Children to health Facility", "20"],
    ["Module 4 Azithromycin Drug Administration and Recording", "27"],
    ["Module 5 Interpersonal Communication and Social and behaviour Change (SBC)", "59"],
    ["Module 6 Safeguarding", "63"],
], 2)

# p3 acronyms
H("Acronyms", 3)
TB(["Acronym", "Meaning"], [
    ["ADR", "Adverse Drug Reactions"], ["AZM", "Azithromycin"], ["CU5", "Children under Five Years"],
    ["CDD", "Community Drug Distributors"], ["EOR", "End of Round"], ["FMoH", "Federal Ministry of Health"],
    ["HF", "Health facility"], ["HFW", "Health facility Worker"], ["IDM", "Institute for Disease Modelling"],
    ["LGA", "Local Government Area"], ["LQAS", "Lots Quality Assurance Sampling"], ["MC", "Malaria Consortium"],
    ["NTD", "Neglected Tropical Disease"], ["RBM", "Roll Back Malaria"], ["SAE", "Severe adverse Reaction."],
    ["SMEP", "State Malaria Elimination program"], ["SPHCDA", "State primary health care Development Agency"],
    ["WHO", "World Health organization"],
], 3)
review(3, "Acronyms", "'LQAS' is spelled out as 'Lots Quality Assurance Sampling' (the usual term is 'Lot Quality "
       "Assurance Sampling') and 'SAE' as 'Severe adverse Reaction.' (usually 'Serious Adverse Event'). Kept as written.")
review(7, "SMS changed to SMC (please confirm)", "Slide 6 lists 'Seasonal Malaria Chemoprevention (SMS)'. Everywhere else the "
       "flipbook uses SMC, so this was treated as a typing error and shown as 'SMC' in the app (see the table above). "
       "'TGE delivery platforms' was likewise shown as 'the delivery platforms'.")

# p4 purpose
H("Purpose of AZM training", 4)
L(["Equip participants with the knowledge and skills needed to properly administer Azithromycin to eligible children during campaign.",
   "Ensure that participants understands proper dosing strategies and schedules for AZM medicines and can recognize when children need to be "
   + fx(4, "refereed", "referred") + " to health facilities.",
   "Train Participants on safeguarding practices to protect children and vulnerable population during AZM drug administration.",
   "Teach proper interpersonal communication technique to effectively educate caregivers about the administration of AZM and their potential side effects.",
   "Provide hands-on practice through demonstration and role plays to build competence in all aspects of AZM drug administration."], 4)

# p5 opener
I("cdd_p05_m1_opener.jpg", "Module 1: Introduction to Azithromycin (AZM) Drug Administration.",
  "Two CDDs in yellow AZM vests talk with a father and a mother holding a young child outside thatched houses; a baby crawls on a mat.", 5)
H("Module 1: Introduction to Azithromycin (AZM) Drug Administration", 5)

# p6 contents and tools
L(["What is the meaning of AZM?", "What is AZM used for?", "What age group can receive AZM?",
   "What is the duration of AZM administration to eligible children?", "How is AZM administered to eligible children?",
   "What is the delivery strategy and platforms for AZM"], 6, title="Contents")
L(["AZM Job Aid.", "Sample of AZM POS", "DIGIT HCM App"], 6, title="Tool for each participant")

# p7
H("Introduction to drug administration of Azithromycin", 7)
T("AZM means Azithromycin.", 7, title="Meaning of AZM")
L(["Azithromycin is a broad-based spectrum antibiotic which is effective in the prevention and treatment of various bacterial "
   "infections including acute lower respiratory tract infections, skin and soft tissue and gastro-enteric infections.",
   "It offers broad benefits including protection against malaria caused by Plasmodium falciparum.",
   "Azithromycin reduces childhood mortality by preventing and treating childhood infections such as pneumonia, diarrhoea and malaria."],
  7, title="Purpose of AZM drug administration")
TF("1.1")  # module quiz 1.1
T("AZM Drug Administration is aimed protection children aged 1-59 months of age from childhood infections.", 7,
  title="Target age group for AZM " + fx(7, "adminsitration", "administration"))
L(["The intervention " + fx(7, "id delivered", "is delivered") + " through door-to-door approach by trained Community Drug "
   "Distributors, under the supervision of the CDD supervisors, LGA, State and National teams.",
   "The AZM administration is done using the Technology app (DIGIT HCM) installed in the devices of the CDDs."],
  7, title="Delivery strategies for AZM")
TF("1.2")  # module quiz 1.2
TF("1.3")  # module quiz 1.3
T("AZM POS means Azithromycin Powdered Oral Suspension", 7, title="What is AZM POS")
T("AZM is administered every six-months (Bi-annually) to children 1 to 59 months of age.", 7,
  title="Duration of AZM drug administration")
L(["AZM MDA will leverage on the following child health interventions:",
   "Neglected tropical disease (NTDs).", "Polio Eradication Initiative campaign.",
   "Seasonal Malaria Chemoprevention (" + fx(7, "SMS", "SMC") + ").", "Maternal Newborn and Child health (MNCH).",
   "Leveraging on these platforms will reduce operational costs, maximizes resources, enhance coverage by minimizing missed "
   "opportunities and maximizing health benefits to eligible populations."],
  7, title="What are " + fx(7, "TGE", "the") + " delivery platforms for AZM MDA")
review(7, "Wording", "The target age group sentence reads 'AZM Drug Administration is aimed protection children aged 1-59 months' "
       "(a word seems to be missing, e.g. 'aimed at protecting'). Kept as written.")

# p8 key takeaways
C("Key take away from module 1",
  "1. Azithromycin (AZM) is given to children within the age group of 1-59 months. 2. The medicine is for the prevention of "
  "pneumonia, diarrhoea and Malaria. 3. It is delivered using Door to door approach by CDDs under the supervision of the CDD "
  "supervisors. 4. The medicine is administered two times a year (every six months) using the DIGIT HCM app.", 8)

# ---------------------------------------------------------------- Module 2
module("CDD-02", 2, "CDD - Module 2: Determination of Eligibility for Azithromycin (AZM) Drug Administration",
       "Who can receive AZM, how to find a child's age, who must not receive AZM, and the MUAC nutrition check.", 40)

I("cdd_p09_m2_opener.jpg", "Module 2: Determination of Eligibility for Azithromycin (AZM) Drug Administration.",
  "A CDD in an orange hijab and yellow vest shows an AZM box to a mother, a baby and a small girl in a yellow dress.", 9)
H("Module 2: Determination of Eligibility for Azithromycin (AZM) Drug Administration", 9)

# p10
L(["Age eligibility for AZM Drug Administration", "How to determine a child's age.",
   "Children that are NOT eligible for AZM during campaign", "Summary of child eligibility for AZM."], 10, title="Contents")
L(["AZM Job Aid"], 10, title="Tools for each participant")

# p11
H("Age eligibility for Azithromycin (AZM) administration during " + fx(11, "CAMAPAIGN", "campaign"), 11)
L(["AZM is given to only healthy children between 1 to 59 months of age.",
   "Children who are less than one month or older than 59 months are not eligible.",
   "Children who are 59 months old in round one should receive AZM but will not be eligible in the next round.",
   "Neonates who are less than one month are not eligible."], 11, title="Eligibility age range for Children to receive AZM")
TF("2.1")  # module quiz 2.1
L(["The safety protocol for AZM has been established for children 1 months and above.",
   "Younger children are more susceptible to potential side effects.",
   "Children between 1 to 59 months are at the highest risk of severe malaria and other childhood infections",
   "The age group experience the highest mortality rates from childhood infections.",
   "It is easier to monitor and " + fx(11, "manager", "manage") + " potential side effects in this age group "
   + fx(11, "(1-59 months.", "(1-59 months).")], 11, title="Why only children 1 to 59 months are eligible for AZM")
L(["Ask to see the child's child health card.", "Ask the caregiver the age of the child.", "Use calendar of events."],
  11, title="What are the ways to determine the age of a child")
L(["Cannot hold head and neck steady when held upright."], 11, title="How to know if an infant is between 1 to 2 months")
L(["Can hold head and neck steady when held upright."], 11, title="How to know if an infant is between 3 to 4 months")
L(["Can hold head and neck steady when held upright.", "Can crawl.", "Can sit without help."], 11,
  title="How to know if an infant is between 3 to 11 months")
L(["Can stand, walk or run.", "Not able to raise the arm and touch the opposite side of the ear.", "Not able to stand on one leg."],
  11, title="How do you know if a child is between 12 to 59 months")
L(["Can raise the arm and touch the opposite side of the ear.", "Can stand on one leg for 10 secs.", "Can jump on one leg.",
   "They are not eligible for AZM MDA."], 11, title="How to know children older than 59months")
review([11, 15], "Age limit (contradiction)", "Slide 10 says children 'older than 59 months' are not eligible; slide 14 says "
       "'Children from 60 months and older' should not be given AZM. A child aged 59 months and some days falls differently under "
       "each wording. Both kept as written.")
review([11, 12], "Age bands overlap (contradiction)", "Slide 10 gives '3 to 4 months' and '3 to 11 months' as two bands with the "
       "same first sign, so they overlap. The slide 11 picture uses '3 to 4 months' and '5 to 11 months' instead, which matches the "
       "dosing bands (1-2, 3-4, 5-11 months). Kept as written.")

# p12 picture
H("How to determine child's age for AZM drug administration", 12)
I("cdd_p12_age_signs.png",
  "How to determine a child's age. Children 1 to 11 months: child 1 to 2 months cannot hold head and neck steady when upright; "
  "NOT newborn or less than one month; child 3 to 4 months can hold head and neck steady when upright; child 5 to 11 months can "
  "crawl and can sit without help. Child 12 to 59 months: can stand or walk; CANNOT raise arm and touch opposite ear; CANNOT stand "
  "or jump on one foot.",
  "Illustrated age guide: a baby lying down (1 to 2 months), a crossed-out newborn, a baby held sitting (3 to 4 months), a baby "
  "crawling and a child sitting (5 to 11 months); below, children standing and walking (12 to 59 months), a crossed-out child "
  "touching the opposite ear and a crossed-out child standing on one foot.", 12)

# p13
H("Children that are not eligible for AZM drug administration", 13)
W("Sick children", "Do NOT give AZM to children who are sick.", 13)
TF("2.2")  # module quiz 2.2
W("Severe Acute Malnutrition (SAM)",
  "Do NOT give AZM to children who are suffering from Severe Acute Malnutrition (SAM):", 13)
L(["Advise the caregiver to take the child to the nearest " + fx(13, "heath", "health") + " facility for further evaluation.",
   "Complete the referral form and give to the caregiver to take to the health facility.",
   "Do not give the caregiver the AZM medicine to administer later or the child record card."], 13)
W("Allergy to AZM or macrolide antibiotics",
  "Do NOT give AZM to children who are allergic to AZM or other macrolide antibiotics.", 13)
L(["Does the Child get sick after taking antibiotic medicines or similar medications.",
   "Has the child taken AZM or similar antibiotics before, If so, did the child get sick after taking them or had reactions such as "
   "rashes, swelling or difficulty breathing."], 13, title="ASK the Caregiver")

# p14 picture
H("Determination of eligibility for Azithromycin (AZM)", 14)
I("cdd_p14_eligible_not_eligible.png",
  "Eligible for AZM: healthy children from a young baby to a standing child. NOT eligible for AZM: difficulty in swallowing, "
  "severe acute malnutrition, not eating, very sick, fever.",
  "Top row with a green tick: a sleeping baby, a baby held sitting, a crawling baby, a sitting child and a standing boy. Bottom row "
  "with a red cross: drawings labelled difficulty in swallowing, severe acute malnutrition, not eating, very sick and fever.", 14)

# p15
H("Children that are not eligible for AZM drug administration", 15)
W("Antibiotics in the last 28 days",
  "Do not give AZM to children who have taken antibiotics " + fx(15, "of similar medication", "or similar medication")
  + " in the last 28 days or 4 weeks or one month.", 15)
L(["Has the child taken any medicine in the last 28 days or 4 weeks.",
   "If yes, what medicine has the child taken in the past one month.", "If possible, ask to see the packet for confirmation."],
  15, title="Ask the caregiver")
L([fx(15, "Visible sever wasting;", "Visible severe wasting;"), "The child looks extremely thin.",
   "The ribs, shoulder blades and bones are very prominent.",
   "The arms and thigh look like “skin and bones” with little or no muscle or flesh.",
   "The child's buttock may appear flat or baggy."], 15,
  title="Children not eligible for AZM MDA due to malnutrition: how to identify a child with severe acute malnutrition (Look and Feel Approach)")
L(["Press gently with your thumb on the top of both feet for about 3 seconds.",
   "If a pit remains after removing the thumb, oedema is present.", "This indicates that the child has Kwashiorkor, a form of SAM."],
  15, title="Bilateral Pitting Oedema")
TF("2.3")  # module quiz 2.3
W("AZM should not be given to the following children",
  "Children from 60 months and older. Children that are allergic to AZM or similar antibiotics. Children who are sick or have "
  "fever. Children who have received AZM or other antibiotics in the last one month. Children who are currently taking AZM or "
  "other antibiotics. Children who cannot swallow.", 15)

# p16 summary
H("Summary of child eligibility for AZM", 16)
I("cdd_p16_eligibility_summary.png",
  "Summary of child eligibility for AZM, with Eligible and Refer columns.",
  "A table of drawings with ticks and crosses: children 1 to 59 months eligible; sick, fever, allergy or malnutrition not eligible "
  "and referred; AZM or similar antibiotics in the last 28 days not eligible.", 16)
TB(["Situation", "Eligible", "Refer"], [
    ["Between 1 to 59 months", "Yes", ""],
    ["When the child is sick", "No", "Yes"],
    ["When the child has fever", "No", "Yes"],
    ["When the child has allergy to antibiotics or similar medicines or has mild/severe/acute malnutrition", "No", "Yes"],
    ["When the child has taken AZM or other similar antibiotics in the last 28 days (4 weeks)", "No", ""],
], 16, title="Summary of child eligibility for AZM", transcribed=True)
review([16, 18], "Malnutrition (possible contradiction)", "Slide 15 marks 'mild/severe/acute malnutrition' as not eligible and "
       "referred. Slides 12 and 14 exclude only Severe Acute Malnutrition (SAM), and slide 17 sends Moderate Acute Malnutrition (MAM) "
       "to the facility for counselling without saying whether AZM is given. Kept as written.")

# p17-p20 MUAC (Section 2 of Module 2)
H("Section 2: MUAC assessment", 17)
L(["Trained CDDs.", "Established supervision structures.", "Kobo Collect digital data platform.",
   "Existing household engagement processes.", "No additional household visits will be required."], 17,
  title="1. MUAC Assessment and Data Collection within SARMAAN II Workflow: the assessment will be implemented within routine "
        "SARMAAN II household visits, leveraging")
T("Mid-Upper Arm Circumference (MUAC) using standard colour-coded MUAC tapes.", 17,
  title="2. " + fx(17, "MAUC", "MUAC") + "/Nutrition Assessment (Children 6–59 months): Measurement")
L(["Left arm.", "Correct midpoint.", "Tape applied lightly or comfortably, not tight or too tight."], 17, title="Measurement protocol")
T("Kobo Collect will automatically classify MUAC values using WHO/UNICEF thresholds.", 17, title="Automated classification")
review(17, "Data tool (Kobo Collect vs DIGIT HCM)", "The MUAC section (slides 16 and 39) says data go into Kobo Collect, while the rest "
       "of the flipbook records children in the DIGIT HCM app. Kept as written; please confirm which tool CDDs use for MUAC.")
review(17, "MUAC age range", "MUAC applies to children 6-59 months, while AZM eligibility is 1-59 months. Kept as written.")

H(fx(18, "MAUC", "MUAC") + "/Nutrition Assessment (Children 6–59 months)", 18)
TB(["MUAC Range", "Status", "Classification", "Action Required"], [
    ["≥ 12.5 cm", "Well-nourished", "Normal", "No immediate action"],
    ["11.5 - 12.4 cm", "At Risk / MAM", "Moderate Acute Malnutrition", "Immediate referral to health facility for counselling"],
    ["< 11.5 cm", "SAM", "Severe Acute Malnutrition", "Immediate referral to health facility"],
], 18, title="MUAC ranges and action required", transcribed=True)
I("cdd_p18_muac_table.png", "MUAC ranges: green 12.5 cm or more (normal), yellow 11.5 to 12.4 cm (MAM), red below 11.5 cm (SAM).",
  "The original MUAC table with green, yellow and red rows for MUAC range, status, classification and action required.", 18)

I("cdd_p19_muac_right_wrong.jpg",
  "MUAC assessment, right and wrong. Good MUAC assessment: left arm, not too tight. Bad MUAC assessment: right arm, too tight.",
  "Two illustrations side by side: a CDD measuring a girl's left arm loosely (good), and a CDD measuring a girl's right arm too "
  "tightly (bad).", 19)
I("cdd_p20_cdd_taking_muac.jpg", "A CDD taking MUAC reading of a child within the age group 6-59 months.",
  "Close-up of hands wrapping a MUAC tape around a child's upper arm.", 20)
I("cdd_p20_muac_tape.jpg", "MUAC Tape.",
  "Diagram of a UNICEF MUAC tape with a red section from 6 to 11 cm, a yellow section at 12 cm and a green section from 13 to 26 cm.", 20)

# ---------------------------------------------------------------- Module 3
module("CDD-03", 3, "CDD - Module 3: Steps for Referral of Children to Health Facility",
       "When and how to refer a sick child or a child with a suspected reaction, and how to fill the AZM referral form.", 30)

I("cdd_p21_m3_opener.jpg", "Module 3: Steps for referral of Children to health facility.",
  "A CDD in a yellow AZM vest holds a referral form and points the way while a mother holds a small child, with another CDD beside her.", 21)
H("Module 3: Steps for referral of Children to health facility", 21)

# p22
H("Steps for referral of children to health facility", 22)
L(["When to refer a sick child.", "When to refer children for possible adverse drug reactions due to AZM.", "AZM referral steps.",
   "How to complete the AZM Referral Form.", "When to complete PV Form and Med Safety App for AZM (for HFWs only)."], 22, title="Contents")
L(["AZM Job Aid.", "AZM Referral Form."], 22, title="Tools for each participant")
I("cdd_p22_referral_photo.jpg", "A CDD explaining a referral to a caregiver.",
  "A CDD in a yellow AZM vest holding a paper and pointing, talking with a mother who holds a small child.", 22)
review([22, 26], "HFW-only items in the CDD book", "Slide 21 lists 'When to complete PV Form and Med Safety App for AZM (for HFWs "
       "only)', and the referral form on slide 25 has a part 'To be completed by the Health Facility Worker'. The CDD flipbook has no "
       "slide that teaches the PV form or Med Safety App. Kept as written.")

# p23
H("When to refer a sick child", 23)
L(["Convulsion.", "Fever or high temperature.", "Difficulty breathing.", "Difficulty staying awake.", "Vomiting.",
   "Not able to eat or drink.", "Severe pains or bleeding.", "Neck pain or severe headache.", "Severe Acute Malnutrition"],
  23, title="Explain what it means when a child is sick or has danger signs")
L(["Children with fever may likely have malaria or other childhood infections.",
   "Malaria, pneumonia and diarrhoea remain the leading causes of death among under five children in Nigeria.",
   "Children with fever needs to be evaluated to avoid complications.",
   "Children with severe acute malnutrition following the nutrition screening using a MUAC tape should be excluded, further "
   "evaluation conducted and receive the required support (resuscitation, feeding programme, etc.)"],
  23, title="EXPLAIN why children needs to be referred to the nearest health facility")
TF("3.1")  # module quiz 3.1
I("cdd_p23_sick_danger_fever.png", "Refer: when the child is sick, when the child has danger signs, when the child has fever.",
  "Two drawings with green ticks: a mother holding a sick baby, labelled when the child is sick or has danger signs, and a boy "
  "holding his forehead, labelled when the child has fever.", 23)

# p24
H("When to refer children to health facility", 24)
T("Allergies to AZM are rare but may occur.", 24, title="STEP 1: Explain that some children may have allergy to AZM")
TF("3.3")  # module quiz 3.3
T("Children need to be referred to the nearest health facilities if they have side effects or suspected adverse reactions.", 24,
  title="STEP 2: Explain that Children need to be referred to the nearest health facilities if they have side effects or suspected adverse reactions")
L(["Swelling of the face, mouth, tongue or other parts of the body.", "Nausea or continuous vomiting.",
   "Skin rashes or blistering of the skin.", "Body itching.", "Weakness or fatigue", "Loss of appetite.",
   "Abdominal pains, Diarrhoea.", "Headache.", "Yellowing of the skin or eyes."], 24,
  title="Show and describe some possible allergy to AZM or reasons for exclusion")
I("cdd_p24_allergy_exclusion_signs.png",
  "Signs to show: very sick, fever, swelling, rash; difficulty in swallowing, severe acute malnutrition, not eating, very sick, fever.",
  "Two rows of drawings: a sick baby, a boy with fever, a boy with a swollen face and a boy with a rash; below, line drawings of "
  "difficulty swallowing, severe acute malnutrition, not eating, a very sick baby and fever.", 24)

# p25
H("Referral steps during AZM campaign", 25)
L(["Do not Give AZM.", "Complete the top portion of the referral form.",
   "Explain to the caregiver the reason for the referral and the need to respond immediately.",
   "If the child has fever, or severe acute malnutrition, explain to the caregivers that the child could have malaria or other "
   "diseases and could get worse or even result in death if not treated immediately.",
   "Tell the caregiver how to get to the nearest health facility.",
   "Give AZM referral form to the caregiver to take to the health facility.",
   "Explain to the caregiver that the health worker will evaluate the child at the facility."], 25,
  title="Explain the steps for referral to the health facilities for children who are sick, or have severe acute malnutrition or suspected adverse reactions")
TF("3.2")  # module quiz 3.2
I("cdd_p25_referral_steps.png", "Do not give AZM, then fill the referral form, then explain the referral to the caregiver.",
  "Three pictures joined by arrows: AZM being poured with a red cross, a health worker filling a form, and a health worker "
  "explaining a form to a seated mother.", 25)

# p26
H("Completing the top section of the AZM referral form", 26)
I("cdd_p26_referral_form.png", "The AZM Referral Form. The top part is completed by the CDD; the lower part by the Health Facility Worker.",
  "The printed AZM Referral Form with logos, a section to be completed by the CDD (child's name, beneficiary ID, age, gender, "
  "state, LGA, ward, settlement, date of referral, facility, AZM round, reason for referral, CDD team code, signature) and a "
  "section to be completed by the Health Facility Worker.", 26)
T("Each CDD team will have a referral forms which are double carbon copy.", 26, title="Explain")
L(["To track the " + fx(26, "umber", "number") + " of children referred to the health facility.",
   "To track the number of children who get to the health facility."], 26,
  title="Ask what is the purpose of AZM " + fx(26, "REFERAL", "referral") + " form")
L(["Show how to complete the top portion of the AZM referral form for the CDDs.",
   "Let the CDDs practice how to fill the top portion of the form."], 26, title="Demonstrate and practice")
C("Role play", "Instruct the CDDs to role play how to give the caregivers referral instructions for this scenario: The Child is "
  "2 years old and has had high fever for 2 days.", 26)

# p27
C("Key take away of module 3",
  "1. Refer children who are sick or malnourished to the nearest health Facility. 2. Fill out the referral form and give to the "
  "caregiver to take to the health facility. 3. Explain the reason for referral to the caregiver and encourage them to take the "
  "child to the health facility immediately.", 27)
