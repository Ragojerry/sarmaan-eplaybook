"""M5-M9 - English content from FLIPBOOK HFW (PDF pages 61-88)."""
from hfw_dsl import C, H, I, L, T, TB, W, audience, module

# ---------------------------------------------------------------- M5
module("M5", "Pharmacovigilance: Reporting Side Effects and Adverse Effects from AZM Drug Administration",
       "Drug safety during AZM, side effects and adverse events, NAFDAC reporting, and the role of DSNOs.")
audience("general", evidence="Inferred: drug-safety basics apply to every role (not in the spec default list)")
I("m5_p61_01.jpg", "Possible side effects — watch children after AZM and refer any child who becomes unwell.",
  "Six drawn panels: a sad child sitting by a puddle, a man holding a crying baby, a girl in bed offered water, a child on a bed given a cup, a girl kneeling and holding her stomach near a latrine, and a woman holding her stomach in pain.", 61)
H("Drug safety during AZM", 63)
T("Drug safety means monitoring and managing the risks of medicines, so the benefits outweigh any harm.", 63)
TB(["Term", "Meaning"],
   [["Side effects", "Minor, expected reactions to medicines that do not require stopping treatment."],
    ["Adverse events", "Can be serious or non-serious."],
    ["Serious adverse event", "Any untoward medical occurrence at any dose resulting in death, hospitalization or longer hospitalization, persistent or significant disability or incapacity, or congenital anomaly or birth defect."]],
   63, title="Side effects and adverse events")
W("Report serious adverse events immediately", "Serious adverse events must be reported immediately.", 63)
L(["Pharmacovigilance aims at rational and safe use of medicines.",
   "It assesses and communicates the risks and benefits of medicines, to improve patient care and public health.",
   "No drug is always safe for everyone.",
   "Know the possible side effects, monitor children, and refer them immediately to the health facility."], 63, title="Objectives of pharmacovigilance")
audience("health_worker", evidence="p22 'When to complete PV Form and Med Safety App for AZM (for HFWs only)'", inferred=False)
H("NAFDAC Med Safety App", 64)
T("The Med Safety app is a free smartphone app for reporting suspected adverse effects.", 64)
L(["Report adverse effects to medicines.", "Keep track of previously reported information.",
   "Receive official news and alerts about medicines.",
   "Download it from the Google Play store on Android or the App Store on iOS."], 64, title="The app lets users")
I("m5_p64_01.png", "Step — open the NAFDAC ADR e-reporting form online, accept the terms, then choose who is reporting.",
  "Small browser screenshot of the NAFDAC ADR eReporting Form with the NAFDAC crest, a confidentiality notice, an I accept the terms checkbox and two green buttons.", 64,
  flag="Screenshot shows a personal browser bookmarks bar; low resolution.")
L(["NAFDAC ADR eReporting Form.",
   "All information provided is treated in strict confidentiality and will not attract any legal liability.",
   "I accept the terms & conditions. View the terms & conditions.",
   "Buttons: I'm reporting for myself or a relative. I'm reporting as a health professional.",
   "The web address and browser tabs are not readable."], 64, title="Screenshot text (transcribed from image; partly readable)", transcribed=True)
L(["Go to the NAFDAC website.", "Click on ADR e-reporting online.", "Complete the form online and submit."], 64, title="Practical demo")
audience("health_worker", evidence="p65 'Section 2: For Health Workers only'", inferred=False)
H("Completing the NAFDAC e-reporting link (for health workers only)", 65)
L(["Objective: strengthen pharmacovigilance by making it easy to report suspected ADRs during the AZM MDA.",
   "State teams ensure all OICs, DSNOs and CDD supervisors have access to the link.",
   "They support health facility OICs to upload all suspected ADR cases to the NAFDAC portal.",
   "Click the link to open the page and start."], 67)
I("m5_p66_01.jpg", "Vomiting after AZM — record it and report a suspected ADR.",
  "Photo of a toddler in a yellow vest vomiting into a blue basin while an adult supports the child.", 66,
  flag="Empty blue caption box below this photo in the PDF.")
L(["Initials: instead of the child's initials, write the State code.",
   "State codes: Kaduna-KD, Kebbi-KB, Jigawa-JG, Adamawa-AD, and Gombe-GOM and SARMAAN II. Example: KB(SARMAAN II).",
   "Sex: Male, Female, or Unknown if you are not sure.", "Weight: the weight of the child in kg.",
   "Date of birth (compulsory): date, month and year."], 67, title="User of the medicine")
L(["Age at time of reaction: enter the age, then choose year, months, week, day or hours.",
   "For SARMAAN II, the child must be between 1-59 months.",
   "Country where the reaction started: select Nigeria."], 67, title="User of the medicine, continued")
L(["Name of the health facility, LGA and State, e.g. From Musa PHC in Soba LGA, Kaduna State.",
   "Reactions/symptoms, such as vomiting, rashes, fever or diarrhoea.",
   "Start date and end date of the reaction (date, month and year).",
   "Duration: enter a number, then choose year, month, days, weeks or hours.",
   "Outcome (recovered, recovering, recovered with lasting effects, or fatal) and Serious: YES or NO."], 68, title="Description (click NEXT to continue)")
L(["Medicine name, e.g. Azithromycin. Tick Probably causing the reaction if you believe the AZM MDA caused it.",
   "Medicine producer: the company name on the AZM bottle. Batch number: from the bottle.",
   "Dosage: the dose given, e.g. 2ml. How administered: select Oral.",
   "Start date: the day the medicine was given. End date: the same day, because it is given once.",
   "Duration: select one Day."], 68, title="Medicines (click NEXT to continue)")
L(["Reason for taking the medicine: AZM MDA for prevention of Pneumonia, Diarrhoea and Malaria in the SARMAAN II Project.",
   "Actions taken: select Not applicable.",
   "Additional information: describe any current or previous illness of the child."], 69, title="Reason and additional information")
L(["Profession: select the role.", "Given name and family name of the reporting officer.",
   "Health facility name.", "Email and phone number of the reporting officer.",
   "Click Submit and wait for the notification that confirms it was submitted."], 69, title="Contact details and submit")
T("https://vigiflow-eforms.who-umc.org/ng/adr", 69, title="NAFDAC e-reporting link")
audience("health_worker", evidence="p70 'ROLE OF DSNOs IN REPORTING SUSPECTED ADVERSE DRUG REACTIONS IN HEALTH FACILITIES'; spec default: DSNO role is health_worker", inferred=False)
H("Role of DSNOs in ADR reporting", 70)
L(["Serve as focal persons for referral to health facilities.",
   "Work with CDD supervisors and teams to identify and refer sick children to the nearest facility.",
   "Follow up so all referred cases get care at the nearest supported facility.",
   "Check with OICs that referred children reported and received appropriate care.",
   "Document referral data in the approved reporting template."], 71)
L(["Ensure OICs promptly report all confirmed ADRs on the NAFDAC platforms (Med Safety app or e-reporting link).",
   "Collect completed pharmacovigilance forms from health facilities and submit them to NAFDAC."], 71, title="Reporting to NAFDAC")
L(["The State DSNO works with LGA DSNOs to get feedback and solve referral problems.",
   "LGA DSNOs join evening review meetings to update on referrals, challenges and support needed.",
   "LGA DSNOs work with CDD supervisors to find and follow up referred cases until upload on the NAFDAC platform.",
   "LGA DSNOs get OIC feedback for upward referral, recovery status and NAFDAC upload.",
   "Work with the LGA team and community leaders on caregivers' reluctance and knowledge barriers."], 72, title="Tracking referred cases")
T("Submit the referral template to the State M&E, copying the DPHC and NTD coordinator.", 72)

# ---------------------------------------------------------------- M6
module("M6", "Interpersonal Communication and Social and Behaviour Change (SBC)",
       "Good communication with caregivers and the SBC methods used in the AZM campaign.")
audience("general", evidence="Spec default: M6 IPC/SBC is general")
I("m6_p73_01.jpg", "Do talk with caregivers respectfully and explain AZM clearly.",
  "Photo of a woman CDD in an orange headscarf and yellow vest gesturing as she talks with a seated mother holding a baby and a standing girl in a yellow dress.", 73)
H("Why interpersonal communication matters", 75)
L(["Good communication builds trust and helps make sure AZM is given safely.",
   "Respect the cultural norms of the community.",
   "Greet the head of household and caregivers with respect, and recognize the child.",
   "Use words they will understand, and use the pictures in the AZM job aid.",
   "Use open-ended questions to get more information."], 75)
L(["Listen carefully to what the head of household or caregiver says.",
   "Give time to answer, and show you are listening by nodding or saying \"I understand\".",
   "Stop from time to time to ask if they understand or have any questions."], 75, title="Listen and check")
L(["Ask the caregiver to repeat the information about AZM.", "Ask questions that get the answers you need.",
   "Let others share information without interruption.", "Explain health messages so they are understood."], 75, title="Exercise: confirm understanding")
L(["Protects children from pneumonia, diarrhoea and malaria.", "Prevents and treats other bacterial infections."], 75, title="Explain the benefits of AZM")
TB(["Type of question", "Examples"],
   [["Closed-ended: gets a yes or no answer", "Is your child between 1 to 59 months? Is your child sick today? Did you have any problems with the last round of AZM?"],
    ["Open-ended: gets more information", "How old is your child? How is your child feeling today? How did your child feel after the last round of AZM?"]],
   75, title="Closed and open-ended questions")
H("Social and behaviour change (SBC)", 76)
T("SBC is a strategic approach that influences behaviour by engaging communities through tailored messages.", 76)
L(["Interpersonal communication.", "Mass media campaigns.", "Community mobilization.", "Visual aids."], 76, title="SBC methods in the AZM campaign")
L(["Ask participants which SBC tools for AZM MDA they have seen or used.",
   "Show examples of AZM job aids, posters and banners used in the community."], 76, title="Facilitator activity")

# ---------------------------------------------------------------- M7
module("M7", "Monitoring and Supervision during AZM Campaign",
       "What supervisors do, the levels of supervision, and the competencies supervisors must show.")
audience("supervisor_monitor", evidence="p78-80 'supervisors'; spec default: M7 is supervisor_monitor", inferred=False)
I("m7_p77_01.jpg", "Supervision — data teams and field supervisors check AZM delivery in real time.",
  "Two photos joined: above, people working at laptops in an operations room with a wall screen; below, two women in vests and a man in a green cap looking at a phone outdoors.", 77)
H("What supervision is", 79)
T("Supervision is coordinated oversight of drug administration, logistics, data collection and community engagement. It makes sure all activities run effectively and efficiently.", 79)
L(["Accurate administration of AZM.", "Compliance with safety protocols and timely reporting of adverse drug reactions.",
   "Supply chain monitoring to prevent stock-outs and wastage.", "Real-time data accuracy and decisions using DIGIT HCM.",
   "Structured e-supervisory checklists and quality assurance."], 79, title="Effective supervision improves")
L(["On-the-job mentoring and training for CDDs and health facility workers.",
   "Community engagement to build caregiver compliance and trust."], 79, title="Effective supervision also provides")
L(["Conduct daily field visits to monitor drug administration and community engagement.",
   "Verify real-time recording of drug administration by CDDs in DIGIT HCM.",
   "Complete and submit supervision checklists with the e-checklist.",
   "Check adherence to dosage protocols and safety measures.",
   "Identify and resolve logistical and operational challenges in real time."], 79, title="Key actions supervisors must take")
L(["Work closely with the LGA and community stakeholders to improve implementation.",
   "Attend review meetings and escalate challenges.", "Provide immediate feedback."], 79, title="Key actions, continued")
H("Levels of supervision", 80)
TB(["Level", "Responsibilities"],
   [["LGA level", "Ensure supervisory plans are followed, logistics are coordinated and CDDs are supported. Monitor daily operations, distribution and community sensitization. Conduct field visits and submit structured supervision checklists."],
    ["Health facility level", "Support CDDs in drug administration, record keeping and referral of suspected adverse reactions. Ensure pharmacovigilance measures are in place. Review DIGIT HCM entries for data accuracy."],
    ["State and National level", "Provide high-level coordination, policy guidance and overall campaign evaluation. Use administrative and supervision data for drug administration tracking and supervisory analysis."]],
   80, title="Levels of supervision in AZM campaign")
L(["Describe the purpose and significance of supervision in the campaign.",
   "Conduct effective field supervision that ensures compliance with protocols.",
   "Use DIGIT HCM for real-time recording of AZM drug administration.",
   "Identify and resolve implementation challenges during the campaign.",
   "Mentor and guide CDDs and other health workers to improve performance."], 80, title="Competencies supervisors must demonstrate")

# ---------------------------------------------------------------- M8
module("M8", "Supply Chain Management during AZM MDA Campaign",
       "What supply chain management means for AZM and how to manage AZM supplies.")
audience("logistician", evidence="Spec default: M8 supply chain is logistician")
I("m8_p81_01.jpg", "Supply chain — AZM cartons are unloaded and stacked on pallets for distribution.",
  "Photo of a worker in a yellow vest and blue gloves unloading cardboard cartons from a white truck onto wooden pallets.", 81)
H("Supply chain management in AZM", 83)
T("Supply chain management in AZM is the coordination and oversight of AZM procurement, distribution and use. It covers the whole campaign.", 83)
L(["Forecasting demand.", "Distribution logistics.", "Inventory management.",
   "Reconciliation and accountability of medicines.", "Data tracking."], 83, title="Why it is important")
L(["Timely availability of medicines.", "Fewer stock-outs and less overstocking that may lead to wastage.",
   "Efficient distribution.", "Data-driven decision making.", "Support for training and enhanced accountability."], 83, title="How it affects AZM effectiveness")
L(["Forecasting.", "Procurement planning.", "Storage and inventory management.", "Distribution logistics.",
   "Training and capacity building."], 83, title="How to manage AZM supplies")
L(["Monitoring and evaluation."], 83)

# ---------------------------------------------------------------- M9
module("M9", "Safeguarding",
       "Protecting children and vulnerable adults during the AZM campaign, and how to report concerns.")
audience("general", evidence="Spec default: M9 safeguarding is general")
I("m9_p84_01.jpg", "Do give AZM from the cup while the child sits upright. Do not force medicine into a lying child's mouth.",
  "Three photos. A mother gives a seated boy medicine from a cup. A green tick over a girl drinking from a cup among children and caregivers. A red X over an adult forcing liquid from a spoon into a lying baby's mouth.", 84)
H("What safeguarding means", 86)
L(["Safeguarding is an organization's commitment that staff and activities do not harm children and vulnerable adults.",
   "It means not exposing them to abuse, harm, risk or exploitation.",
   "It protects the rights and dignity of all, especially children and vulnerable adults."], 86)
L(["Respectful interaction with caregivers and their families.", "Educating community members on the benefits of AZM.",
   "Addressing caregivers' concerns about the AZM campaign.", "Ensuring informed consent from caregivers.",
   "Handling AZM medicines safely during the campaign."], 86, title="Examples of safeguarding")
H("Protection during the AZM campaign", 86)
T("Protection means taking action when children or vulnerable people are at risk or experience harm.", 86)
L(["Ensure only eligible children receive AZM.", "Give the correct dose.", "Prevent overdosing during MDA.",
   "Refer sick children to the nearest health facility."], 86, title="Immediate safety measures")
H("Safeguarding during the campaign", 87)
L(["Select CDDs with active community involvement, so they represent the community and act with integrity.",
   "Caregivers have the right to informed consent, dignity and respect. They can know the names of the CDD and supervisors.",
   "Give caregivers complete, accurate information, including risks and what to do after an adverse reaction.",
   "Caregivers need a way to get support or raise concerns and complaints.",
   "The consent form should list a few designated contacts they can reach."], 87)
W("Never force AZM", "CDDs must not force AZM on caregivers or treat children harshly.", 87)
I("m9_p88_01.jpg", "Do not take pictures without consent.",
  "Photo of a man holding a camera to his face, with a large red X over it.", 88)
I("m9_p88_02.jpg", "Do not take pictures without consent, including with a phone.",
  "Photo of a person holding up a smartphone to take a picture in a dry field, with a large red X over it.", 88)
I("m9_p88_03.jpg", "Do not take or give bribes. Avoid all corrupt practices, sexual harassment and exploitation.",
  "Close-up photo of hands holding a bundle of Nigerian 1000 naira notes, with a large red X over it.", 88)
W("Avoid corrupt practices",
  "Avoid bribery and all forms of corrupt practices in the field, including sexual harassment and exploitation.", 88)
H("Reporting safeguarding issues", 87)
L(["Report all safeguarding issues to the CDD supervisor or health facility OIC.",
   "They escalate it to the NTD coordinator of the LGA team and partners.",
   "Report any case or suspected case of violence or neglect of eligible children to the health facility OIC.",
   "The OIC escalates it to Malaria Consortium through the appropriate MoH structures."], 87)
C("Report safeguarding issues", "Report all safeguarding issues to concenrns@malariaconsortium.org.", 87)
