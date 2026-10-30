"""
Seeds a starter quiz for each module M1-M6. EVERY question is drawn from the
module's own text (the explanation quotes the source), covering all seven
question types. Idempotent: modules that already have questions are skipped
(use --replace to rebuild one's questions).

These are DRAFT-QUALITY starter questions written from the training text. A
programme/technical reviewer should read them before real rollout, and edit them
in Admin > Content > (module) > Quiz.

Usage: cd backend && python -m scripts.seed_quizzes [--replace]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import MediaAsset, Module, QuizQuestion
from app.models.enums import QuestionType as T
from app.quiz.grading import validate_content


def mc(prompt, options, correct, why):
    return (T.MULTIPLE_CHOICE, prompt, {"options": options, "correct": correct}, why)


def tf(prompt, correct, why):
    return (T.TRUE_FALSE, prompt, {"correct": correct}, why)


def ms(prompt, options, correct, why):
    return (T.MULTIPLE_SELECT, prompt, {"options": options, "correct": correct}, why)


def match(prompt, pairs, why):
    return (T.MATCHING, prompt, {"pairs": [{"left": a, "right": b} for a, b in pairs]}, why)


def order(prompt, items, why):
    return (T.ORDERING, prompt, {"items": items}, why)


def num(prompt, correct, unit, why, tol=0):
    return (T.NUMERIC, prompt, {"correct": correct, "tolerance": tol, "unit": unit}, why)


def img(prompt, filename, alt, options, correct, why):
    return (T.IMAGE_CHOICE, prompt, {"image": filename, "alt": alt, "options": options, "correct": correct}, why)


QUIZZES = {
    "M1": [
        mc("What does AZM stand for?", ["Azithromycin", "Artemether-Zinc Medicine", "Amoxicillin-Zinc Mixture", "Anti-Zinc Malaria tablet"], 0,
           "\"AZM stands for Azithromycin, a broad-spectrum antibiotic.\""),
        tf("AZM Drug Administration targets children aged 1–59 months.", True,
           "\"AZM Drug Administration targets children aged 1–59 months.\""),
        mc("How often is AZM given to a child?", ["Once a month", "Every three months", "Once every six months (bi-annually)", "Once a year"], 2,
           "\"It is given once every six months (bi-annually).\""),
        ms("Which common childhood infections does azithromycin help prevent and treat?", ["Malaria", "Pneumonia", "Diarrhoea", "Measles"], [0, 1, 2],
           "\"Azithromycin reduces childhood mortality by preventing and treating common childhood infections — Malaria, Pneumonia and Diarrhoea.\""),
        match("Match each term to its meaning.",
              [("CDD", "Community Drug Distributor"), ("POS", "Powdered Oral Suspension"),
               ("DIGIT HCM", "App used for administration and reconciliation")],
              "CDDs deliver AZM door-to-door; the sample medicine is the AZM Powdered Oral Suspension (POS); administration and reconciliation are done in the DIGIT HCM app."),
        img("What is happening in this picture?", "module1-hero.jpg",
            "A CDD in a yellow AZM vest talking with a family in their compound",
            ["A CDD introduces the AZM visit to a household before assessing the children",
             "A CDD is mixing the medicine", "A supervisor is checking returned bottles", "A caregiver is filling in a referral form"], 0,
            "Module 1 caption: \"a CDD introduces the AZM visit to a household before assessing the children present.\""),
        tf("AZM is only given at the health facility, never door-to-door.", False,
           "\"Door-to-door, by trained Community Drug Distributors (CDDs).\""),
        num("AZM is given bi-annually. How many months apart are the rounds?", 6, "months",
            "\"It is given once every six months (bi-annually).\""),
        tf("AZM also offers some protection against malaria caused by Plasmodium falciparum.", True,
           "\"It also offers some protection against malaria caused by Plasmodium falciparum.\""),
        mc("Who supervises the CDDs?", ["Health workers, LGA, State and National teams", "Other CDDs only", "Caregivers", "Nobody; CDDs work alone"], 0,
           "CDDs are \"supervised by health workers, LGA, State and National teams.\""),
    ],
    "M2": [
        tf("A child who is 60 months old is eligible for AZM.", False,
           "\"Children younger than 1 month, or 60 months and older, are not eligible.\""),
        ms("Which of these children are NOT eligible for AZM?",
           ["A child with fever", "A healthy 8-month-old", "A child who took AZM 3 weeks ago", "A child who cannot swallow"], [0, 2, 3],
           "Not eligible: sick or fever; took AZM or a similar antibiotic in the last 28 days; cannot swallow."),
        num("A child is not eligible if they took AZM or a similar antibiotic within how many days?", 28, "days",
            "\"Children who have taken AZM or a similar antibiotic in the last 28 days (4 weeks).\""),
        match("Match each age group to the milestone used to estimate age.",
              [("1–2 months", "Cannot hold head/neck steady upright"), ("3–4 months", "Can hold head/neck steady upright"),
               ("5–11 months", "Can crawl and sit unaided"), ("12–59 months", "Can stand, walk or run")],
              "Age-estimation guide in \"Age eligibility\"."),
        img("What is the CDD doing in this picture?", "module2-muac.jpg",
            "A CDD taking a MUAC reading on a child's left arm using a colour-coded tape",
            ["Taking a MUAC reading on the child's left arm", "Measuring height with the dose pole",
             "Checking the child's health card", "Giving the AZM dose"], 0,
            "Module 2 caption: \"wrap the tape around the left upper arm at the correct midpoint.\""),
        mc("A MUAC reading below 11.5 cm means:",
           ["Severe Acute Malnutrition: refer to health facility immediately", "Normal: no action",
            "Moderate Acute Malnutrition: counselling only", "The tape was used incorrectly"], 0,
           "\"< 11.5 cm — Severe Acute Malnutrition — Refer to health facility immediately.\""),
        mc("A MUAC reading of 11.5–12.4 cm means:",
           ["Moderate Acute Malnutrition: refer to health facility for counselling", "Severe Acute Malnutrition",
            "Normal: no immediate action", "The child is not eligible for MUAC"], 0,
           "\"11.5 – 12.4 cm — Moderate Acute Malnutrition — Refer to health facility for counselling.\""),
        tf("MUAC is measured on the child's right arm.", False,
           "CDDs take a MUAC reading \"using the left arm and a colour-coded tape.\""),
        mc("MUAC readings are taken for children aged:", ["6–59 months", "1–5 months", "12–24 months only", "All ages including adults"], 0,
           "\"a Mid-Upper Arm Circumference (MUAC) reading for children 6–59 months.\""),
        order("Put these MUAC readings in order from highest to lowest.",
              ["≥ 12.5 cm: Normal", "11.5 – 12.4 cm: Moderate Acute Malnutrition", "< 11.5 cm: Severe Acute Malnutrition"],
              "Order of the MUAC classification table."),
    ],
    "M3": [
        ms("Which of these are danger signs that need referral?",
           ["Convulsion", "Difficulty breathing", "Difficulty staying awake", "Playing happily"], [0, 1, 2],
           "Danger signs: convulsion, difficulty breathing, difficulty staying awake, vomiting everything, unable to drink or feed, severe pain/bleeding, neck pain or severe headache."),
        order("Put the referral steps in the correct order.",
              ["Do NOT give AZM", "Complete the top portion of the AZM Referral Form", "Explain the reason for referral and its urgency",
               "Direct the caregiver to the nearest facility", "Confirm the caregiver understands by asking them to repeat the instructions",
               "Give them the referral form to take along"],
              "\"Referral steps\": 1) Do NOT give AZM ... 6) Give them the referral form to take along."),
        tf("A child who has a fever should be given AZM.", False, "\"Refer any child who is sick, has danger signs ... or has fever.\""),
        mc("How do you confirm the caregiver understood the referral instructions?",
           ["Ask them to repeat the instructions", "Ask if they have any questions and move on", "Give them a leaflet", "Call their supervisor"], 0,
           "\"Confirm the caregiver understands by asking them to repeat the instructions.\""),
        img("What is the CDD doing in this picture?", "module3-referral.jpg",
            "A CDD explaining a referral to a caregiver holding a child, pointing to the referral form",
            ["Explaining a referral to a caregiver using the AZM Referral Form", "Measuring the child's dose",
             "Chalk-marking a house", "Taking a MUAC reading"], 0,
            "Module 3 caption: \"a CDD explains why a child is being referred, using the AZM Referral Form.\""),
        ms("Which could be signs of an allergic reaction to AZM?",
           ["Swelling of the face, mouth or tongue", "Skin rash, itching or blistering", "Yellowing of the skin or eyes", "Normal, playful behaviour"], [0, 1, 2],
           "\"Possible signs of an allergic reaction to AZM\" lists swelling, rash/itching/blistering and yellowing of skin or eyes."),
        num("Nausea or severe vomiting for more than how many hours is a possible sign of an allergic reaction?", 2, "hours",
            "\"nausea or severe vomiting for more than 2 hours.\""),
        tf("When referring a sick child, you should hand over the Child Record Card.", False,
           "\"do not hand over the Child Record Card when referring a sick child — complete the AZM Referral Form instead.\""),
        mc("What do you give the caregiver to take to the health facility?",
           ["The completed AZM Referral Form", "The Child Record Card", "A bottle of AZM", "Nothing"], 0,
           "\"Give them the referral form to take along.\""),
        tf("CDDs should leave their phone numbers on the child record card so caregivers can reach them if a referral is needed later.", True,
           "\"CDDs should leave their phone numbers on the child record card.\""),
    ],
    "M4": [
        num("How much clean water is used to reconstitute the AZM powder?", 15, "ml",
            "\"Reconstitute with 15 ml of clean water to obtain a 30 ml suspension.\""),
        num("Each reconstituted bottle serves how many children?", 4, "children", "\"Each bottle serves 4 children.\""),
        match("Match each age to its AZM dose.",
              [("1–2 months", "2 ml"), ("3–4 months", "3 ml"), ("5–11 months", "4 ml")], "Dosing strategy table."),
        num("What dose, in ml, does a 4-month-old child receive?", 3, "ml", "\"3–4 months: 3 ml.\""),
        order("Put the safe-administration steps in order.",
              ["Sit the child upright", "Give the dose slowly with the dispensing cup", "Make sure the child swallows it all",
               "Re-dose if the child vomits within 5 minutes", "Observe the child for 30 minutes for any side effect"],
              "\"Safe administration\" callout."),
        num("A child must be re-dosed if they vomit within how many minutes?", 5, "minutes",
            "\"re-dose if the child vomits within 5 minutes.\""),
        ms("At the end of the day, which AZM bottles must be returned and reconciled?",
           ["Empty bottles", "Partially used bottles", "Unopened bottles", "None; unopened bottles can be kept at home"], [0, 1, 2],
           "\"All AZM bottles issued each morning must be returned — empty, partially used, or unopened.\""),
        img("What does this picture show?", "module4-give-slowly.jpg",
            "A caregiver giving AZM slowly to a child who is sitting upright",
            ["AZM given slowly, cup to lip, with the child sitting upright", "A child being measured with the dose pole",
             "A CDD mixing the powder", "A caregiver filling in the record card"], 0,
            "Module 4 caption: \"AZM is given slowly, cup to lip, with the child sitting upright and properly positioned.\""),
        mc("A house marked AZM/26/1/56708/021/3/1/R means:",
           ["It needs a revisit: only 1 of 3 eligible children dosed", "Completed: all 3 eligible children dosed",
            "All children were excluded", "The house was refused"], 0,
           "\"AZM/26/1/56708/021/3/1/R — needs a revisit, only 1 of 3 dosed.\""),
        tf("The Child Record Card is kept by the caregiver for two years across all four rounds.", True,
           "\"kept by the caregiver for two years across all four rounds.\""),
        mc("How do you find the dose for a child aged 12–59 months?",
           ["Use the dose pole to measure height", "Always give 4 ml", "Ask the caregiver", "Use the child's weight from the card"], 0,
           "\"For children 12–59 months, use the dose pole to measure height.\""),
        tf("Partially used bottles stay viable for up to 2 days.", True, "\"Partially used bottles stay viable for up to 2 days.\""),
    ],
    "M5": [
        mc("Which is a CLOSED question used to confirm information?",
           ["\"Is your child sick today?\"", "\"How old is your child?\"", "\"Tell me about your family.\"", "\"What do you know about AZM?\""], 0,
           "closed questions (\"Is your child sick today?\") confirm information."),
        mc("Which is an OPEN-ENDED question used to gather information?",
           ["\"How old is your child?\"", "\"Is your child sick today?\"", "\"Is the child 2 years old?\"", "\"Do you agree?\""], 0,
           "open-ended questions (\"How old is your child?\") gather information."),
        match("Match each type of question to its purpose.",
              [("Open-ended question", "Gather information"), ("Closed question", "Confirm information")],
              "\"Use open-ended questions ... to gather information, and closed questions ... to confirm it.\""),
        ms("Which are good interpersonal communication practices?",
           ["Greet the head of household and caregivers respectfully", "Use language they understand and the job-aid pictures",
            "Ask the caregiver to repeat key information back", "Interrupt to save time"], [0, 1, 2],
           "Good IPC: greet respectfully, use understandable language and pictures, listen without interrupting, check understanding by asking them to repeat."),
        tf("To check that a caregiver understood, ask them to repeat the key information back.", True,
           "\"check the caregiver has understood by asking them to repeat key information back.\""),
        mc("What is Social & Behaviour Change (SBC)?",
           ["A strategic approach that influences behaviour by engaging communities through tailored messaging", "A type of medicine",
            "A form for referring children", "A method of measuring doses"], 0,
           "\"SBC is a strategic approach that influences behaviour by engaging communities through tailored messaging.\""),
        ms("SBC combines which of these?",
           ["Interpersonal communication", "Mass media", "Community mobilisation", "Visual aids such as the job aid, posters and banners", "Ignoring community feedback"],
           [0, 1, 2, 3], "SBC combines \"interpersonal communication, mass media, community mobilisation, and visual aids.\""),
        img("What does this picture show?", "module5-ipc.jpg",
            "A CDD speaking with a caregiver holding two children, using open hands in a respectful, explanatory manner",
            ["A CDD speaking respectfully with a caregiver and checking she has understood", "A CDD measuring a child's arm",
             "A supervisor reconciling bottles", "A CDD chalk-marking a wall"], 0,
            "Module 5 caption: \"good IPC means open, respectful questions and checking the caregiver has understood.\""),
        tf("A CDD should listen without interrupting the caregiver.", True, "\"Listen without interrupting.\""),
        mc("Who should a CDD greet respectfully on arrival?",
           ["The head of household and caregivers", "Only the youngest child", "Only neighbours", "Nobody; start the assessment straight away"], 0,
           "\"Greet the head of household and caregivers respectfully.\""),
    ],
    "M6": [
        mc("What does safeguarding mean?",
           ["Ensuring staff and programme activities never harm children or vulnerable adults, or expose them to abuse, risk or exploitation",
            "Keeping the AZM bottles locked away", "Making sure every house is chalk-marked", "Reporting dose errors to the supervisor"], 0,
           "\"Safeguarding is the commitment to ensure staff and programme activities never harm children or vulnerable adults.\""),
        ms("Which are rights of caregivers?",
           ["Informed consent", "Respectful treatment", "Knowing the CDD's and supervisor's names", "Being forced to give AZM"], [0, 1, 2],
           "\"Caregivers have the right to informed consent, respectful treatment, and to know both the CDD's and supervisor's names.\""),
        tf("A CDD may take photographs of children without consent.", False, "Avoid: \"Taking photographs without consent.\""),
        mc("Who do you escalate a safeguarding issue to?",
           ["Your CDD supervisor or health facility OIC", "A neighbour", "Nobody; handle it yourself", "The caregiver"], 0,
           "\"Escalate any safeguarding issue to your CDD supervisor or health facility OIC.\""),
        img("What is wrong in this picture?", "module6-wrong.jpg",
            "Giving medicine with a metal spoon rather than the provided dispensing cup",
            ["Medicine is given with a metal spoon instead of the provided dispensing cup", "The child is sitting upright",
             "The caregiver is holding the child", "Nothing is wrong"], 0,
            "Module 6 caption: \"Avoid — using an improvised spoon instead of the provided dispensing cup.\""),
        img("Why is this the correct method?", "module6-right.jpg",
            "A caregiver giving AZM with the proper dispensing cup, child calm and properly held",
            ["The proper cup is used, the child is calm and the caregiver is in control", "It uses an improvised spoon",
             "The child is lying flat", "The CDD is holding the child by force"], 0,
            "Module 6 caption: \"Correct — the proper cup, child calm, caregiver in control throughout.\""),
        order("Put the escalation of a safeguarding issue in order.",
              ["You notice a safeguarding issue", "You report it to your CDD supervisor or health facility OIC",
               "They raise it to the LGA NTD coordinator and partners"],
              "\"Escalate ... to your CDD supervisor or health facility OIC, who will raise it to the LGA NTD coordinator and partners.\""),
        tf("Accepting a bribe is acceptable if a caregiver offers it as thanks.", False,
           "Avoid: \"any bribery or corrupt practice, including sexual harassment or exploitation, in the field.\""),
        mc("Which email address can a safeguarding concern be sent to directly?",
           ["concerns@malariaconsortium.org", "info@azm.org", "supervisor@lga.gov", "help@digit.org"], 0,
           "\"email concerns@malariaconsortium.org directly.\""),
        ms("Which must a CDD avoid?",
           ["Taking photographs without consent", "Any bribery or corrupt practice", "Sexual harassment or exploitation", "Using the provided dispensing cup"],
           [0, 1, 2], "\"Avoid — Taking photographs without consent · any bribery or corrupt practice, including sexual harassment or exploitation.\""),
        tf("CDDs are selected with active community involvement, on the basis of integrity and community trust.", True,
           "\"CDDs are selected with active community involvement, on the basis of integrity and community trust.\""),
    ],
}


def run(replace=False):
    db = SessionLocal()
    try:
        assets = {a.filename: a for a in db.query(MediaAsset).all()}
        for code, questions in QUIZZES.items():
            module = db.query(Module).filter_by(module_code=code).one_or_none()
            if module is None:
                print(f"{code}: module not found, skipped")
                continue
            existing = db.query(QuizQuestion).filter_by(module_id=module.id).count()
            if existing and not replace:
                print(f"{code}: already has {existing} questions, skipped")
                continue
            if existing:
                db.query(QuizQuestion).filter_by(module_id=module.id).delete()
            for i, (qtype, prompt, content, why) in enumerate(questions, start=1):
                content = dict(content)
                if qtype == T.IMAGE_CHOICE:
                    asset = assets.get(content.pop("image"))
                    if asset is None:
                        raise SystemExit(f"{code} question {i}: picture missing from the media library")
                    content["media_asset_id"] = str(asset.id)
                db.add(QuizQuestion(module_id=module.id, question_type=qtype, prompt=prompt,
                                    content=validate_content(qtype, content), explanation=why, sort_order=i))
            db.commit()
            print(f"{code}: {len(questions)} questions")
    finally:
        db.close()


if __name__ == "__main__":
    run(replace="--replace" in sys.argv)
