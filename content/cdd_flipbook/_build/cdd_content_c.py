"""CDD flipbook, PDF pages 60-68: Modules 5 and 6."""
from cdd_dsl import TF, C, H, I, L, T, W, module, review

# ---------------------------------------------------------------- Module 5
module("CDD-05", 5, "CDD - Module 5: Interpersonal Communication and Social and Behaviour Change (SBC)",
       "Talking with caregivers respectfully and clearly, open and closed questions, and SBC methods in the AZM campaign.", 25)

I("cdd_p60_m5_opener.jpg", "Module 5: Interpersonal communication and Social behaviour (SBC).",
  "A CDD in an orange hijab and yellow vest talks with a mother holding a baby, with a girl in a yellow dress beside them.", 60)
H("Module 5: Interpersonal communication and Social behaviour (SBC)", 60)
review([2, 60], "Module 5 title", "The contents page calls Module 5 'Interpersonal Communication and Social and behaviour Change "
       "(SBC)'; its opening slide says 'Interpersonal communication and Social behaviour (SBC)'. The module name in the app uses the "
       "contents-page wording; both are kept in the text.")

L(["Introduction to Interpersonal Communication", "Guidelines for Using Good IPC with Caregivers",
   "Social and behavior change in AZM campaign"], 61, title="Contents")
L(["AZM Job Aid"], 61, title="Tools for each participant")

H("Introduction to interpersonal communication", 62)
L(["Good communication helps to build trust and ensure that AZM is given safely.", "Respect cultural norms of the community.",
   "Greet the head of the household and caregivers with respect and recognize the child.",
   "Use words the head of household and caregivers will understand.", "Use the pictures in the AZM job aid to communicate",
   "Use open ended questions to get more information.", "Listen carefully to what the head of household or caregiver tells you.",
   "Allow time for the caregiver to answer questions and show that you are listening by nodding your head or saying I understand.",
   "Stop from time to time to ask the caregiver if he/she understand or has any question."], 62,
  title="Explain the importance of interpersonal communication in AZM MDA")
TF("6.1")  # module quiz 6.1
TF("6.2")  # module quiz 6.2
L(["Ask questions in a way that helps to get the answers you need.",
   "Listen to others and allow them to share information without interruption.",
   "Explain health messages in a way that should be understood."], 62,
  title="Exercise: ask the caregiver to repeat information about AZM to confirm it was understood")
L(["Protects children from pneumonia, diarrhoea and malaria.", "Prevents and treat other bacterial infections."], 62,
  title="Explain the benefits of AZM")
L(["A closed ended questions gets a yes or no answer e.g. is your child between 1 to 59 months?", "Is your child sick today?",
   "Did you have any problems with the last round of AZM."], 62,
  title="Facilitate activity: guidelines for using the IPC with caregivers. Explain the difference between closed and open-ended questions")
L(["How old is your child or what is your child's age.", "How is your child feeling today.",
   "How did your child feel after the last round of AZM?"], 62, title="An open-ended question gets more information: example")

H("Social and behaviour change in AZM campaign", 63)
T("SBC is a strategic approach that aims to influence behaviour by engaging communities through tailored messages.", 63,
  title="Explain what social and behaviour change communication is")
L(["Interpersonal communication.", "Mass media Campaigns.", "Community Mobilization.", "Visual aids."], 63,
  title="Explain what type of SBC communication methods will be used in the AZM campaign")
C("Ask participants", "Ask participants what SBC tools for AZM MDA they have seen or used.", 63)
C("Show examples of SBC tools", "Show examples of AZM Job aids, poster and banner used in the community.", 63)
TF("6.3")  # module quiz 6.3

# ---------------------------------------------------------------- Module 6
module("CDD-06", 6, "CDD - Module 6: Safeguarding",
       "Protecting children and vulnerable adults during AZM MDA, caregivers' rights, and how to report concerns.", 25)

I("cdd_p64_m6_do_dont.jpg",
  "Module 6: Safeguarding. Right (tick): a caregiver gives AZM gently from a cup, and children are given AZM calmly. Wrong (cross): "
  "a crying child held down and given medicine by force with a spoon.",
  "Three photos: top left, a mother gently gives a boy medicine from a cup; top right, children drink medicine near seated women, "
  "with a green tick; bottom, a crying baby held down while medicine is forced in with a spoon, with a red cross.", 64)
H("Module 6: Safeguarding", 64)

H("Safeguarding during AZM MDA and AZM MDA", 65)
review(65, "Duplicated heading", "The heading on slide 64 reads 'Safeguarding during AZM MDA and AZM MDA'. Kept as written.")
L(["Introduction to safeguarding", "Safeguarding during AZM MDA.", "Protection during AZM MDA.", "Safeguarding Case Studies."],
  65, title="Contents")
L(["AZM Job Aid"], 65, title="Tools for each participant")

H("Introduction to safeguarding", 66)
L(["Safeguarding refers to the commitment of an organization to ensure that staff and program activities do not harm children and "
   "vulnerable adults or expose them to potential abuse, harm, risk or exploitation.",
   "It involves the protection of the rights and dignity of all individual especially children and vulnerable adults to ensure that "
   "they are free from abuse, harm and exploitation."], 66, title="What safeguarding means and why it is important")
TF("8.1")  # module quiz 8.1
L(["An organization's resolve to safeguarding children and vulnerable adults from harm and abuse during campaign.",
   "This include upholding and protecting the rights and dignity of all individuals with particular attention to children."],
  66, title="Safeguarding during AZM Campaign: Safeguarding is")
L(["Respectful interaction with caregivers and their families.", "Educating community members on the benefits of AZM.",
   "Addressing concerns of caregivers regarding AZM Campaign.", "Ensuring informed consent from caregivers.",
   "Handling AZM medicines safely during AZM Campaign."], 66, title="Examples of safeguarding")
TF("8.3")  # module quiz 8.3
L(["Protection means taking action when children or vulnerable individuals are found to be at risk or experience harm.",
   "It involves specific measures to address immediate safety concerns such as:",
   "Ensuring that only eligible children receive AZM.", "Administering the correct dose.", "Preventing overdosing during MDA.",
   "Referring sick children to the nearest health facility."], 66, title="Protection during AZM Campaign")
TF("8.2")  # module quiz 8.2

H("Safeguarding case studies", 67)
L(["Ensuring the safe selection of Community volunteers. The selection of CDDs should be carried out with active involvement of the "
   "community to guarantee that those chosen truly represent the community, uphold integrity and are motivated primarily by the "
   "community interest.",
   "Caregivers have the right to give informed consent, treated with dignity and respect, be informed of their rights and know the "
   "names of both the CDD and their supervisors.",
   "Caregivers must be provided with complete and accurate information including potential risks and steps to take in the event of "
   "any adverse reaction.",
   "Caregivers should have the means to contact someone for support, advice, or to raise concerns and complaints if they feel "
   "misinformed or maltreated. The consent form should list few designated contacts they can reach out to for assistance."],
  67, title="Safeguarding during AZM Campaign extends to the following")
W("CDDs must not force AZM", "CDDs must not force AZM on caregivers or treat children harshly.", 67)
L(["All safeguarding issues should be reported to the CDD supervisors or health facility OICs who will scale it up to the NTD "
   "coordinator of the LGA team and partners.",
   "CDDs are required to report any cases or suspected cases of violence or neglect involving eligible children to the health "
   "facility OIC, who will in turn escalate these to malaria consortium through the appropriate MoH structures.",
   "All safeguarding issues should be reported to concenrns@malariaconsortium.org."], 67, title="Reporting safeguarding issues")
review(67, "Safeguarding email address (please confirm)", "The reporting address is printed as 'concenrns@malariaconsortium.org' "
       "in the text layer of slide 66; the slide image shows 'concenrns@' too. It is probably meant to be 'concerns@', but an email "
       "address cannot be corrected without confirmation, so it is kept exactly as printed. Please confirm the correct address.")

I("cdd_p68_no_photos_camera.jpg", "Avoid taking pictures without consent.",
  "A man holding a camera up to his face, crossed out with a red X.", 68)
I("cdd_p68_no_photos_phone.jpg", "Avoid taking pictures without consent.",
  "A hand holding up a mobile phone to take a photo in a field, crossed out with a red X.", 68)
I("cdd_p68_no_bribery.jpg", "Avoid bribery and all forms of corrupt practices in the field including sexual harassment and exploitation.",
  "A hand holding a bundle of naira banknotes, crossed out with a red X.", 68)
L(["Avoid taking pictures without consent", "Avoid bribery and all forms of corrupt practices in the field including sexual "
   "harassment and exploitation."], 68)
