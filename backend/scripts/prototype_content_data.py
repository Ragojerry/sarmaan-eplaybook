"""
Structured content data for Phase 6 migration, transcribed by hand from the
prototype's `modules` array raw HTML bodies (sarmaan-eplaybook-prototype_1.html,
lines ~1015-1213). Hand-transcription rather than an HTML parser was a
deliberate choice: the prototype's body strings are one-off template
literals, not a consistent machine-parseable format, and correctness of the
actual training content matters more here than reusability of a parser that
would only ever run once against this one file.

Every section here maps to a real `ContentType` enum value — no raw HTML is
stored, per master prompt §16. `image` sections reference a photo key,
resolved to a real `media_asset_id` by the import script after it uploads
the actual files. `video` sections reference a video's *prototype index*
(0-3, matching the prototype's `videos` array order), resolved to a real
`video_id` by the import script after it creates the `videos` rows.

A judgment call worth flagging: the prototype used two callout styles —
`callout good` (positive framing: "why it matters", "safe administration")
and plain `callout` (constraints/cautions: "do not", "accountability",
"avoid"). Mapped here as CALLOUT for the "good" variant and WARNING for the
plain variant. This is a reasonable interpretation of unstructured legacy
content, not a specified requirement — content reviewers may want to
recategorize individual sections during Phase 5's governance review.
"""

MODULES = [
    {
        "module_code": "M1",
        "module_number": 1,
        "title": "Introduction to Azithromycin (AZM) Drug Administration",
        "sort_order": 1,
        "speak": (
            "Module 1. Introduction to Azithromycin drug administration. AZM stands for "
            "Azithromycin, a broad-spectrum antibiotic used in the prevention and treatment of "
            "bacterial infections, including lower respiratory tract infections, skin infections, "
            "and gastro-enteric infections. It also offers some protection against malaria. "
            "Azithromycin reduces childhood mortality by preventing and treating Malaria, "
            "Pneumonia, and Diarrhoea. AZM drug administration targets children aged 1 to 59 "
            "months, and it's given once every six months. It is delivered door-to-door by "
            "trained Community Drug Distributors, supervised by health workers and LGA, State "
            "and National teams, using the DIGIT HCM app on the CDD's phone."
        ),
        "sections": [
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module1-hero",
                    "alt": "A CDD in a yellow AZM vest talking with a family in their compound before administering AZM",
                    "caption": "In the field — a CDD introduces the AZM visit to a household before assessing the children present.",
                },
            },
            {"content_type": "HEADING", "content": {"text": "What is AZM?"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": (
                        "AZM stands for Azithromycin, a broad-spectrum antibiotic used in the "
                        "prevention and treatment of bacterial infections including acute lower "
                        "respiratory tract infections, skin and soft-tissue infections, and "
                        "gastro-enteric infections. It also offers some protection against malaria "
                        "caused by Plasmodium falciparum."
                    )
                },
            },
            {
                "content_type": "CALLOUT",
                "content": {
                    "heading": "Why it matters",
                    "text": "Azithromycin reduces childhood mortality by preventing and treating common childhood infections — Malaria, Pneumonia and Diarrhoea.",
                },
            },
            {"content_type": "HEADING", "content": {"text": "Who receives it"}},
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "AZM Drug Administration targets children aged 1–59 months.",
                        "It is given once every six months (bi-annually).",
                    ]
                },
            },
            {"content_type": "HEADING", "content": {"text": "How it's delivered"}},
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "Door-to-door, by trained Community Drug Distributors (CDDs), supervised by health workers, LGA, State and National teams.",
                        "Administration and reconciliation are done through the DIGIT HCM app installed on the CDD's own Android phone.",
                    ]
                },
            },
            {
                "content_type": "JOB_AID",
                "content": {
                    "heading": "Job aid tools",
                    "text": "AZM Job Aid · Sample AZM Powdered Oral Suspension (POS) · DIGIT HCM app",
                },
            },
        ],
    },
    {
        "module_code": "M2",
        "module_number": 2,
        "title": "Determination of Eligibility for AZM Drug Administration",
        "sort_order": 2,
        "speak": (
            "Module 2. Determination of eligibility for AZM drug administration. AZM is given "
            "only to healthy children between 1 and 59 months. Children younger than 1 month, or "
            "60 months and older, are not eligible. To estimate age, ask to see the child's health "
            "card, ask the caregiver, or use a calendar of local events. Children are not eligible "
            "if they are sick, have a fever, have severe acute malnutrition, are allergic to AZM or "
            "similar antibiotics, have taken AZM or a similar antibiotic in the last 28 days, or "
            "cannot swallow. Do not give the caregiver AZM medicine to give later, and do not hand "
            "over the child record card when referring a sick child. Under the SARMAAN-II pilot, "
            "CDDs also take a Mid-Upper Arm Circumference, or MUAC, reading for children 6 to 59 "
            "months, using the left arm and a colour-coded tape. A reading below 11.5 centimetres "
            "means severe acute malnutrition, and requires immediate referral."
        ),
        "sections": [
            {"content_type": "HEADING", "content": {"text": "Age eligibility"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": "AZM is given only to healthy children between 1 and 59 months. Children younger than 1 month, or 60 months and older, are not eligible."
                },
            },
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "Ask to see the child's health card (green card), ask the caregiver, or use a calendar of local events to estimate age.",
                        "1–2 months: cannot hold head/neck steady upright. 3–4 months: can. 5–11 months: can crawl and sit unaided. 12–59 months: can stand, walk or run — but cannot raise an arm over the head to touch the opposite ear, and cannot stand or jump on one foot (that would suggest >59 months, ineligible).",
                    ]
                },
            },
            {"content_type": "HEADING", "content": {"text": "Who is NOT eligible"}},
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "Children who are sick or have fever — refer to the nearest health facility.",
                        "Children with severe acute malnutrition (visible severe wasting or bilateral pitting oedema).",
                        "Children allergic to AZM or similar antibiotics.",
                        "Children who have taken AZM or a similar antibiotic in the last 28 days (4 weeks).",
                        "Children who cannot swallow.",
                    ]
                },
            },
            {
                "content_type": "WARNING",
                "content": {
                    "heading": "Do not",
                    "text": 'Give AZM medicine to the caregiver "to give later," and do not hand over the Child Record Card when referring a sick child — complete the AZM Referral Form instead.',
                },
            },
            {
                "content_type": "VIDEO",
                "content": {"video_index": 1, "title": "Watch: Correct MUAC tape technique", "duration": "1 min 40s"},
            },
            {"content_type": "HEADING", "content": {"text": "SARMAAN-II pilot: MUAC & ANC assessment"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": "Within the same household visit (no extra visit required), CDDs also take a Mid-Upper Arm Circumference (MUAC) reading for children 6–59 months, using the left arm and a colour-coded tape, and confirm a short set of ANC questions for pregnant women."
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module2-muac",
                    "alt": "A CDD taking a MUAC reading on a child's left arm using a colour-coded tape",
                    "caption": "Step — wrap the tape around the left upper arm at the correct midpoint; not too tight, not too loose.",
                },
            },
            {
                "content_type": "TABLE",
                "content": {
                    "headers": ["MUAC range", "Classification", "Action"],
                    "rows": [
                        ["≥ 12.5 cm", "Normal", "No immediate action"],
                        ["11.5 – 12.4 cm", "Moderate Acute Malnutrition", "Refer to health facility for counselling"],
                        ["< 11.5 cm", "Severe Acute Malnutrition", "Refer to health facility immediately"],
                    ],
                },
            },
        ],
    },
    {
        "module_code": "M3",
        "module_number": 3,
        "title": "Steps for Referral of Children to Health Facility",
        "sort_order": 3,
        "speak": (
            "Module 3. Steps for referral of children to health facility. Refer any child who is "
            "sick, has danger signs such as convulsion, difficulty breathing, difficulty staying "
            "awake, vomiting everything, being unable to drink or feed, severe pain or bleeding, "
            "neck pain or severe headache, or who has a fever. Watch for possible signs of an "
            "allergic reaction to AZM: swelling of the face, mouth or tongue, severe vomiting for "
            "more than two hours, skin rash or blistering, severe weakness, abdominal pain, or "
            "yellowing of the skin or eyes. If any of these appear: do not give AZM, complete the "
            "top portion of the AZM Referral Form, explain the reason for referral and its "
            "urgency, direct the caregiver to the nearest facility, confirm they understand by "
            "asking them to repeat the instructions, and give them the referral form to take "
            "along."
        ),
        "sections": [
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module3-referral",
                    "alt": "A CDD explaining a referral to a caregiver holding a child, pointing to the referral form",
                    "caption": "In the field — a CDD explains why a child is being referred, using the AZM Referral Form.",
                },
            },
            {"content_type": "HEADING", "content": {"text": "When to refer"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": "Refer any child who is sick, has danger signs (convulsion, difficulty breathing, difficulty staying awake, vomiting everything, unable to drink or feed, severe pain/bleeding, neck pain or severe headache), or has fever."
                },
            },
            {"content_type": "HEADING", "content": {"text": "Possible signs of an allergic reaction to AZM"}},
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "Swelling of the face, mouth, tongue or other body parts; nausea or severe vomiting for more than 2 hours; skin rash, itching or blistering; severe weakness; loss of appetite; abdominal pain; diarrhoea; headache; unusual behaviour; yellowing of skin or eyes."
                    ]
                },
            },
            {
                "content_type": "WARNING",
                "content": {
                    "heading": "Referral steps",
                    "text": "1) Do NOT give AZM. 2) Complete the top portion of the AZM Referral Form. 3) Explain the reason for referral and its urgency. 4) Direct the caregiver to the nearest facility. 5) Confirm the caregiver understands by asking them to repeat the instructions. 6) Give them the referral form to take along.",
                },
            },
            {
                "content_type": "VIDEO",
                "content": {
                    "video_index": 2,
                    "title": "Watch: Completing the AZM Referral Form",
                    "duration": "2 min 15s",
                },
            },
            {
                "content_type": "TEXT",
                "content": {
                    "text": "CDDs should leave their phone numbers on the child record card so caregivers can reach them if a referral is needed later."
                },
            },
        ],
    },
    {
        "module_code": "M4",
        "module_number": 4,
        "title": "Azithromycin Drug Administration and Recording",
        "sort_order": 4,
        "speak": (
            "Module 4. Azithromycin drug administration and recording. Check the expiry date "
            "before use. Reconstitute the AZM powdered oral suspension with 15 millilitres of "
            "clean water to obtain a 30 millilitre suspension, and shake vigorously. Each bottle "
            "serves 4 children. For children 1 to 2 months, give 2 millilitres. For 3 to 4 months, "
            "give 3 millilitres. For 5 to 11 months, give 4 millilitres. For children 12 to 59 "
            "months, use the dose pole to measure height, and read off the matching dose. Sit the "
            "child upright, give the dose slowly with the dispensing cup, ensure they swallow it "
            "all, re-dose if the child vomits within 5 minutes, and observe for 30 minutes "
            "afterwards. All AZM bottles issued each morning must be returned and reconciled in "
            "DIGIT HCM at day's end. Every visited house is chalk-marked with a code showing the "
            "programme, year, round, team code, house number, and status, so no child is missed."
        ),
        "sections": [
            {"content_type": "HEADING", "content": {"text": "AZM Powdered Oral Suspension (POS)"}},
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "Check the expiry date before use. Reconstitute with 15 ml of clean water to obtain a 30 ml suspension. Each bottle serves 4 children.",
                        "Shake vigorously before each use to keep the suspension consistent.",
                    ]
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module2-dose-measure",
                    "alt": "A CDD measuring out the AZM dose into a dispensing cup",
                    "caption": "Step — measure the exact dose shown by DIGIT HCM using the provided calibrated cup.",
                },
            },
            {
                "content_type": "VIDEO",
                "content": {
                    "video_index": 0,
                    "title": "Watch: Mixing & administering AZM POS",
                    "duration": "2 min 50s",
                },
            },
            {"content_type": "HEADING", "content": {"text": "Dosing strategy"}},
            {
                "content_type": "TABLE",
                "content": {
                    "headers": ["Age (1–11 months)", "Dose"],
                    "rows": [["1–2 months", "2 ml"], ["3–4 months", "3 ml"], ["5–11 months", "4 ml"]],
                },
            },
            {
                "content_type": "TEXT",
                "content": {
                    "text": "For children 12–59 months, use the dose pole to measure height; the DIGIT HCM app (or the pole itself) shows the matching dose."
                },
            },
            {
                "content_type": "CALLOUT",
                "content": {
                    "heading": "Safe administration",
                    "text": "Sit the child upright · give the dose slowly with the dispensing cup · ensure they swallow it all · re-dose if the child vomits within 5 minutes · observe for 30 minutes afterwards for any side effect.",
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module4-give-slowly",
                    "alt": "A caregiver giving AZM slowly to a child who is sitting upright",
                    "caption": "Step — AZM is given slowly, cup to lip, with the child sitting upright and properly positioned.",
                },
            },
            {
                "content_type": "WARNING",
                "content": {
                    "heading": "Accountability",
                    "text": "All AZM bottles issued each morning must be returned — empty, partially used, or unopened — and reconciled in DIGIT HCM at day's end. Partially used bottles stay viable for up to 2 days.",
                },
            },
            {"content_type": "HEADING", "content": {"text": "House-marking codes"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": "Every visited house is chalk-marked so no child is missed: Program / Year / Round / Team code / House no. / Eligible-given / Status"
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module4-housemark",
                    "alt": "A CDD writing a housemarking code in chalk on the wall of a compound",
                    "caption": "Step — mark the house in chalk immediately after the visit — before moving to the next compound.",
                },
            },
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "AZM/26/1/56708/021/3/3/C — completed, all 3 eligible children dosed.",
                        "AZM/26/1/56708/021/3/1/R — needs a revisit, only 1 of 3 dosed.",
                        "AZM/26/1/56708/021/0/0/E — all children excluded.",
                    ]
                },
            },
            {"content_type": "HEADING", "content": {"text": "Recording & cohort tracking"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": "Every child's details, dose and date are recorded on the Child Record Card, kept by the caregiver for two years across all four rounds."
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module4-recordcard",
                    "alt": "A caregiver reading through a completed AZM child record card",
                    "caption": "Step — the completed Child Record Card stays with the caregiver — bring it to every future round.",
                },
            },
            {
                "content_type": "TEXT",
                "content": {
                    "text": "Cohort tracking follows the same children across rounds to monitor safety, coverage and adherence over time."
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module5-cohort",
                    "alt": "A CDD supervisor reviewing DIGIT HCM data on a phone among a group of caregivers and children",
                    "caption": "Why it matters — a child who received AZM last round should also receive it this round, so progress can be tracked reliably.",
                },
            },
        ],
    },
    {
        "module_code": "M5",
        "module_number": 5,
        "title": "Interpersonal Communication and Social & Behaviour Change (SBC)",
        "sort_order": 5,
        "speak": (
            'Module 5. Interpersonal communication and social and behaviour change. Greet the '
            "head of household and caregivers respectfully, using language they understand and "
            'the pictures in the AZM job aid. Use open-ended questions, such as "how old is your '
            'child", to gather information, and closed questions, such as "is your child sick '
            'today", to confirm it. Listen without interrupting, and check the caregiver has '
            "understood by asking them to repeat key information back. Social and behaviour "
            "change, or S B C, is a strategic approach that influences behaviour by engaging "
            "communities through tailored messaging — combining interpersonal communication, "
            "mass media, community mobilisation, and visual aids such as the AZM job aid, posters "
            "and banners."
        ),
        "sections": [
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module5-ipc",
                    "alt": "A CDD speaking with a caregiver holding two children, using open hands in a respectful, explanatory manner",
                    "caption": "In the field — good IPC means open, respectful questions and checking the caregiver has understood.",
                },
            },
            {"content_type": "HEADING", "content": {"text": "Good interpersonal communication (IPC)"}},
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "Greet the head of household and caregivers respectfully; use language they understand and the pictures in the AZM job aid.",
                        'Use open-ended questions ("How old is your child?") to gather information, and closed questions ("Is your child sick today?") to confirm it.',
                        "Listen without interrupting, and check the caregiver has understood by asking them to repeat key information back.",
                    ]
                },
            },
            {
                "content_type": "VIDEO",
                "content": {
                    "video_index": 3,
                    "title": "Watch: Good interpersonal communication in the field",
                    "duration": "1 min 55s",
                },
            },
            {"content_type": "HEADING", "content": {"text": "Social & Behaviour Change (SBC)"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": "SBC is a strategic approach that influences behaviour by engaging communities through tailored messaging — combining interpersonal communication, mass media, community mobilisation, and visual aids such as the AZM job aid, posters and banners."
                },
            },
        ],
    },
    {
        "module_code": "M6",
        "module_number": 6,
        "title": "Safeguarding",
        "sort_order": 6,
        "speak": (
            "Module 6. Safeguarding. Safeguarding is the commitment to ensure staff and programme "
            "activities never harm children or vulnerable adults, or expose them to abuse, risk "
            "or exploitation. During the AZM campaign, CDDs are selected with active community "
            "involvement, on the basis of integrity and trust. Caregivers have the right to "
            "informed consent, respectful treatment, and to know both the CDD's and supervisor's "
            "names. CDDs must never force AZM on a caregiver or treat a child harshly. Avoid "
            "taking photographs without consent, and avoid any bribery or corrupt practice, "
            "including sexual harassment or exploitation, in the field. Report any safeguarding "
            "issue to your CDD supervisor or health facility OIC, or email concerns at "
            "malariaconsortium dot org directly."
        ),
        "sections": [
            {"content_type": "HEADING", "content": {"text": "What safeguarding means"}},
            {
                "content_type": "TEXT",
                "content": {
                    "text": "Safeguarding is the commitment to ensure staff and programme activities never harm children or vulnerable adults, or expose them to abuse, risk or exploitation — protecting the rights and dignity of everyone involved."
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module6-wrong",
                    "alt": "Incorrect method: giving medicine with a metal spoon rather than the provided dispensing cup",
                    "caption": "✕ Avoid — using an improvised spoon instead of the provided dispensing cup.",
                },
            },
            {
                "content_type": "IMAGE",
                "content": {
                    "photo_key": "module6-right",
                    "alt": "Correct method: a caregiver giving AZM with the proper dispensing cup, child calm and properly held",
                    "caption": "✓ Correct — the proper cup, child calm, caregiver in control throughout.",
                },
            },
            {"content_type": "HEADING", "content": {"text": "During the AZM campaign"}},
            {
                "content_type": "LIST",
                "content": {
                    "items": [
                        "CDDs are selected with active community involvement, on the basis of integrity and community trust.",
                        "Caregivers have the right to informed consent, respectful treatment, and to know both the CDD's and supervisor's names.",
                        "Caregivers must be told about potential risks and what to do if a reaction occurs, and must have a way to raise concerns.",
                        "CDDs must never force AZM on a caregiver or treat a child harshly.",
                    ]
                },
            },
            {
                "content_type": "WARNING",
                "content": {
                    "heading": "Avoid",
                    "text": "Taking photographs without consent · any bribery or corrupt practice, including sexual harassment or exploitation, in the field.",
                },
            },
            {
                "content_type": "CALLOUT",
                "content": {
                    "heading": "Report",
                    "text": "Escalate any safeguarding issue to your CDD supervisor or health facility OIC, who will raise it to the LGA NTD coordinator and partners — or email concerns@malariaconsortium.org directly.",
                },
            },
        ],
    },
]

# Prototype `videos` array, in its original index order (0-3) — the
# `video_index` fields above reference these positions.
VIDEOS = [
    {
        "title": "Mixing & administering AZM POS",
        "description": "Step-by-step demonstration: reconstituting the powdered oral suspension, correct positioning, and safe dosing.",
        "module_code": "M4",
    },
    {
        "title": "Correct MUAC tape technique",
        "description": "How to take a Mid-Upper Arm Circumference reading on the left arm without applying it too tight or too loose.",
        "module_code": "M2",
    },
    {
        "title": "Completing the AZM Referral Form",
        "description": "A walkthrough of the CDD and health-facility-worker sections of the referral form.",
        "module_code": "M3",
    },
    {
        "title": "Good interpersonal communication in the field",
        "description": "A role-play demonstration of open- and closed-ended questioning with a caregiver.",
        "module_code": "M5",
    },
]
