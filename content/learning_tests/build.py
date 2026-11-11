"""Builds the General test and the inline module quizzes from the programme's files
(content/source/Test_Questions_for_CDD_Playbook_version_aa_rev_10.11.26.docx and
content/source/Module_Quiz_aa_rev_10.11.26.docx, transcribed below word for word).

Writes, next to this file:
  general_test.json                       the 25 questions (answer key empty: none was supplied)
  general_test_answer_key_TEMPLATE.csv    fill in the "correct_option" column (A-D)
  module_quiz.json                        the 27 True/False statements, their answers and, for the
                                          HFW modules, the section each one follows
and docs/test-content-review.md and docs/module-quiz-map.md.

The CDD statements are placed inside the CDD flipbook content itself
(content/cdd_flipbook/_build/cdd_content_*.py reads module_quiz.json), so run:
  python -I content/learning_tests/build.py
  python -I content/cdd_flipbook/_build/cdd_build.py
  python -I content/learning_tests/build.py      # again, so the map shows the CDD placements
Only obvious spelling/spacing typos are fixed; every change is listed in the review doc.
"""
import csv
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOCS = os.path.join(ROOT, "docs")
NS = uuid.UUID("0b6f2d44-51c3-4e7a-9d1e-a9b1e5c3f7d0")
CHANGES = []  # (where, original, corrected)


def fx(where, original, corrected):
    CHANGES.append((where, original, corrected))
    return corrected


# ------------------------------------------------------------------ General test (25 questions)
# (prompt, [options in printed order], mentions CDDs). "(1 Point)" lines are score markers, not text.
G = [
    ("What does AZM MDA stand for?",
     ["Azithromycin Multi Drug Administration", fx("Q1 option B", "Mass  Administration of Azithromycin ", "Mass Administration of Azithromycin"),
      "Amoxicillin Mass Dosage Assessment", "Amoxicillin Medical Distribution Activity"], False),
    ("What is the target age group for AZM administration?",
     ["6 to 12 months", "1 to 59 months", "3 to 24 months", "5 to 10 years"], False),
    ("Which age group is eligible for the height-based dosing strategy?",
     ["6 to 12 months", "1 to 59 months", "12 to 59 months", "5 to 10 years"], False),
    ("Which of the following represents the correct ages used in the three-tier strategy?",
     ["1-3 months, 4-6 months, 7-11 Months",
      fx("Q4 option B", "1-2months, 3-7months, 8-11months", "1-2 months, 3-7 months, 8-11 months"),
      fx("Q4 option C", "1-2 months, 3-4months, 5-11months", "1-2 months, 3-4 months, 5-11 months"),
      fx("Q4 option D", "1-4months, 5-7months, 8-11months", "1-4 months, 5-7 months, 8-11 months")], False),
    ("Which of the following represents the correct doses used in the three-tier strategy?",
     ["1ml, 2ml, 3ml", "2ml, 3ml, 4ml", "3ml, 4ml, 5ml", "2ml, 4ml, 5ml"], False),
    ("Where should AZM be administered to children?",
     [fx("Q6 option A", "At a Fixed Post ", "At a Fixed Post"), "At the Health Facility", "At the house", "At School"], False),
    ("How many rounds of AZM are there in one Year?", ["1", "4", "2", "3"], False),
    ("What should a CDD (dispenser) do if a child vomits within 5 minutes of taking AZM?",
     ["Re-dose the child", "Ignore and move on", "Wait until the next administration cycle", "Give a double dose immediately"], True),
    (fx("Q9 question", "How does the CDD receive  informed consent from the head of house before  administering AZM?",
        "How does the CDD receive informed consent from the head of house before administering AZM?"),
     ["Head of house or Caregivers are forced to accept the medicine",
      "Head of house or Caregivers are informed of the benefits and risks and asked to agree",
      "Only verbal consent is required from community leaders", "No consent is needed"], True),
    ("Who is responsible for administering AZM in communities?",
     ["Pharmacists", "Community Drug Distributors (CDDs)", "Health Supervisors", "Parents"], False),
    ("Which platform is NOT used to deliver AZM?",
     ["Seasonal Malaria Chemoprevention (SMC)", "Neglected Tropical Diseases (NTD)", "Polio Eradication Initiative (PEI)",
      "School feeding programs"], False),
    ("What should be done if a caregiver refuses AZM for their child?",
     ["Force them to accept it", "Respect their decision but provide more education", "Ignore them and move on",
      "Report them to the authorities"], False),
    ("What is the correct way to mix AZM medicine (powdered oral suspension (POS))?",
     ["Shake the bottle and add 15ml of clean water, then shake again", "Mix with fruit juice", "Heat before use",
      "Pour directly into the child's mouth"], False),
    ("Which child should NOT receive AZM?",
     ["A child with no history of allergies", "A child currently taking antibiotics", "A child who eats well",
      "A child whose sibling has an allergy"], False),
    ("What is the purpose of house marking during the campaign?",
     ["To identify houses where food is available", "To mark houses where AZM has been administered",
      "To warn others of disease outbreaks", "To mark new houses in the community"], False),
    ("Tick the correct House Marking when AZM only is completely given to a household in Round 1",
     ["AZM / 26 / 1 / 56708 / 021/ 0/2 / Complete", "AZM / 26 / 1 / 56708 / 021/ 2/2 / C",
      "AZM / 26 / 1 / 56708 / 021/ 2/2 / E", "AZM / 26/ 1 / 56708 / 021/ 3/2 / C"], False),
    ("What should be done for a child experiencing severe allergic reaction after taking AZM?",
     ["Give another dose", "Report immediately and refer the child to a health facility", "Wait for the reaction to stop",
      "Ignore and continue the campaign"], False),
    ("What is the correct order for administering AZM to a child?",
     ["Determine eligibility, obtain consent, administer the correct dose, and record",
      "Give the medicine first, then ask for consent", "Record first before giving medicine",
      "Ask the community leader for consent"], False),
    ("What should a CDD do if a caregiver is not at home during a visit?",
     ["Administer the medicine to another child", "Mark the house for a revisit", "Skip the house and never return",
      "Give the medicine to a neighbor"], True),
    ("What does PV stand for in the context of drug safety?",
     ["Patient Verification", "Pharmacovigilance", "Public Vaccination", "Pediatric Validation"], False),
    ("Which organization is responsible for reporting adverse drug reactions in Nigeria?",
     ["UNICEF", "WHO", "NAFDAC", "NDLEA"], False),
    ("What is an expected mild side effect of AZM?", ["Loss of vision", "Nausea and diarrhea", "Paralysis", "High fever"], False),
    ("How should unused AZM be handled at the end of each day?",
     ["Thrown away", "Given to the next child", "Returned to the health facility", "Stored at home"], False),
    ("What is the purpose of the AZM Child Record Card?",
     ["To track the administration of AZM", "To register children for school", "To track immunizations",
      "To register children for welfare services"], False),
    ("What is the main goal of the AZM MDA?",
     ["To distribute drugs to children under 5",
      fx("Q25 option B", "To reduce under 5 child mortality ", "To reduce under 5 child mortality"),
      "To reduce above 5 child mortality", "To distribute drugs to children above 5"], False),
]
assert len(G) == 25 and all(len(o) == 4 for _, o, _ in G)
GENERAL_NOTES = {
    10: "The question is general, but the expected answer names CDDs.",
    16: "House marking is a CDD task; health workers and others may not have been taught it. The house-marking "
        "codes in the options are kept exactly as printed (their spacing differs between options).",
    4: "Option A ends with 'Months' (capital M) and the others with 'months'; kept as printed.",
}

# ------------------------------------------------------------------ module quizzes (9 x 3, True/False)
Q = [
    # ref, quiz module, topic as printed, statement, answer
    ("1.1", 1, "Introduction to AZM",
     fx("Quiz 1.1", "AZM  prevents and treats pnuemonia, diarrhoea and malaria in children 1-59 months",
        "AZM prevents and treats pneumonia, diarrhoea and malaria in children 1-59 months"), True),
    ("1.2", 1, "Introduction to AZM", "AZM is delivered through door to door approach", True),
    ("1.3", 1, "Introduction to AZM", "AZM data is collected using Technology App", True),
    ("2.1", 2, "Determination of eligibility for AZM MDA", "AZM is given to all children 1-59 months", False),
    ("2.2", 2, "Determination of eligibility for AZM MDA", "A sick child is eligible for AZM", False),
    ("2.3", 2, "Determination of eligibility for AZM MDA", "A child with SAM is not eligible for AZM", True),
    ("3.1", 3, fx("Quiz 3 topic", "Steps for Refferal of Children to HF", "Steps for Referral of Children to HF"),
     "A sick child should be referred to the Health Facility immediately", True),
    ("3.2", 3, "Steps for Referral of Children to HF",
     fx("Quiz 3.2", "The CDD fills a referal from for the caregiver to take to the HF immediately",
        "The CDD fills a referral form for the caregiver to take to the HF immediately"), True),
    ("3.3", 3, "Steps for Referral of Children to HF", "Allergies to AZM are rare but may occur", True),
    ("4.1", 4, "AZM Administration and recording",
     fx("Quiz 4.1", "The age or height of the child isused to calcute the dose of AZM to be given",
        "The age or height of the child is used to calculate the dose of AZM to be given"), True),
    ("4.2", 4, "AZM Administration and recording", "House marking helps keep track of the children reached and households visited", True),
    ("4.3", 4, "AZM Administration and recording",
     fx("Quiz 4.3", "There is no re-dosing in AZM administaration ", "There is no re-dosing in AZM administration"), False),
    ("5.1", 5, "PharmacoVigilance: Reporting side effects and adverse effects", "Reporting on adverse drug reactions should be to NAFDAC portal", True),
    ("5.2", 5, "PharmacoVigilance: Reporting side effects and adverse effects", "Reporting on adverse drug reaction is paper-based only", False),
    ("5.3", 5, "PharmacoVigilance: Reporting side effects and adverse effects", "DSNOs are responsible for ADR tracking and reporting", True),
    ("6.1", 6, "Interpersonal Communication and SBC", "CDDs should disregard cultural norms when at the household", False),
    ("6.2", 6, "Interpersonal Communication and SBC",
     "CDDs should seek consent from the head of the household for administering AZM to eligible children", True),
    ("6.3", 6, "Interpersonal Communication and SBC",
     fx("Quiz 6.3", "Job Aids are an important tool for explaining the AZM administaration to caregivers",
        "Job Aids are an important tool for explaining the AZM administration to caregivers"), True),
    ("7.1", 7, "Supply Chain Management", "OICs are to confirm and ensure documentation of AZM bottles received", True),
    ("7.2", 7, "Supply Chain Management", "OICs are to document commodities issued to CDD on ICC", True),
    ("7.3", 7, "Supply Chain Management", fx("Quiz 7.3", "Empty bottles of AZM are to be thrown away ", "Empty bottles of AZM are to be thrown away"), False),
    ("8.1", 8, "Safeguarding", "Safeguarding means protecting only children from harm and abuse", False),
    ("8.2", 8, "Safeguarding", "Protection involves specific measures to address immediate safety concerns during AZM MDA", True),
    ("8.3", 8, "Safeguarding", "Safeguarding entails interacting respectfully with caregiver", True),
    ("9.1", 9, "Monitoring and Supervision during AZM Campaign", "Supervision improves quality of AZM MDA", True),
    ("9.2", 9, "Monitoring and Supervision during AZM Campaign", "CDD Supervisors only monitor community engagement", False),
    ("9.3", 9, "Monitoring and Supervision during AZM Campaign", "There is only one level of supervision during MDA", False),
]
assert len(Q) == 27

# Quiz module -> module (programme decision 2026-11-10: by topic; Supply Chain -> HFW-10, where it is taught).
HFW_MODULE = {1: "HFW-01", 2: "HFW-02", 3: "HFW-04", 4: "HFW-06", 5: "HFW-13", 6: "HFW-14", 7: "HFW-10", 8: "HFW-17", 9: "HFW-15"}
CDD_MODULE = {1: "CDD-01", 2: "CDD-02", 3: "CDD-03", 4: "CDD-04", 6: "CDD-05", 8: "CDD-06"}
# HFW placement: statement -> the section (number in content/hfw_flipbook) it follows, with a note.
HFW_AFTER = {
    "1.1": (11, ""), "1.2": (16, ""), "1.3": (16, ""),
    "2.1": (3, ""), "2.2": (18, ""), "2.3": (27, ""),
    "3.1": (9, ""), "3.3": (12, ""), "3.2": (20, ""),
    "4.1": (14, ""), "4.3": (18, ""),
    "4.2": (23, "HFW-06 does not teach house marking (that is HFW-08, Monitor/Supervisor only). Kept at the end of "
                "HFW-06 by programme decision (2026-11-11): not moved, and no line added to HFW-06."),
    "5.1": (6, ""), "5.2": (16, ""), "5.3": (19, ""),
    "6.1": (3, ""),
    "6.2": (3, "Consent is taught in HFW-17 Safeguarding, not in HFW-14; placed after the section on greeting the head of household."),
    "6.3": (11, ""),
    "7.1": (3, ""), "7.2": (3, ""), "7.3": (6, ""),
    "8.1": (3, ""), "8.3": (4, ""), "8.2": (7, ""),
    "9.1": (4, ""), "9.2": (6, ""), "9.3": (9, ""),
}
CDD_NOTES = {
    "6.2": "The CDD Module 5 (interpersonal communication) does not mention consent; informed consent is taught in CDD "
           "Module 6 (Safeguarding). Placed after the section on respecting the household.",
}


def section_id(module_code, ref):
    return str(uuid.uuid5(NS, f"{module_code}/quiz/{ref}"))


def build():
    hfw = {m["module_code"]: m for m in json.load(open(os.path.join(ROOT, "content", "hfw_flipbook", "content_sections.json"),
                                                         encoding="utf-8"))}
    general = [{"number": n, "prompt": p, "options": o, "cdd_specific": c, "correct_index": None}
               for n, (p, o, c) in enumerate(G, 1)]
    statements = []
    for ref, qm, topic, text, answer in Q:
        entry = {"ref": ref, "quiz_module": qm, "topic": topic, "statement": text, "answer": answer, "placements": []}
        if qm in HFW_MODULE:
            code = HFW_MODULE[qm]
            n, note = HFW_AFTER[ref]
            anchor = hfw[code]["sections"][n - 1]
            entry["placements"].append({"audience": "HFW", "module_code": code, "section_id": section_id(code, ref),
                                        "after_section_id": anchor["id"], "after_section_number": n, "note": note})
        if qm in CDD_MODULE:
            code = CDD_MODULE[qm]
            entry["placements"].append({"audience": "CDD", "module_code": code, "section_id": section_id(code, ref),
                                        "note": CDD_NOTES.get(ref, "")})
        statements.append(entry)
    with open(os.path.join(HERE, "general_test.json"), "w", encoding="utf-8") as f:
        json.dump(general, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "module_quiz.json"), "w", encoding="utf-8") as f:
        json.dump(statements, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, "general_test_answer_key_TEMPLATE.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["number", "question", "A", "B", "C", "D", "correct_option"])
        for q in general:
            w.writerow([q["number"], q["prompt"], *q["options"], ""])
    return hfw, general, statements


def section_label(s):
    c = s["content"]
    text = s.get("title") or c.get("text") or c.get("heading") or "; ".join(c.get("items", [])[:2]) or c.get("caption") or ""
    return f"#{s['section_number']} {s['content_type']}: {text[:90]}"


def quiz_map(hfw, statements):
    cdd_path = os.path.join(ROOT, "content", "cdd_flipbook", "content_sections.json")
    cdd = {m["module_code"]: m for m in json.load(open(cdd_path, encoding="utf-8"))} if os.path.exists(cdd_path) else {}
    out = ["# Module quiz placement", "",
           "Source: `content/source/Module_Quiz_aa_rev_10.11.26.docx` (9 modules x 3 True/False statements, with its answer key).",
           "Mapping confirmed 2026-11-10: HFW and others get the nine quizzes, matched to the HFW modules by topic "
           "(Supply Chain Management in HFW-10 Drug Accountability, where its points are taught); CDD gets quizzes 1-4, "
           "6 (IPC and SBC) and 8 (Safeguarding). Each statement follows the section that teaches it.",
           "Generated by `content/learning_tests/build.py`.", "",
           "## Mapping", "", "| Quiz module | Topic | HFW module | CDD module |", "|---|---|---|---|"]
    topics = {}
    for s in statements:
        topics.setdefault(s["quiz_module"], s["topic"])
    for qm, topic in topics.items():
        h = HFW_MODULE.get(qm)
        c = CDD_MODULE.get(qm)
        out.append(f"| {qm} | {topic} | {h} {hfw[h]['title']} | {(c + ' ' + cdd[c]['title']) if c and c in cdd else (c or 'not for CDD')} |")
    out += ["", "Who sees a quiz is decided by the module's own audience: e.g. HFW-13 and HFW-06 quizzes reach the roles that "
            "see those modules (see docs/roles-and-tests.md).", "",
            "## Placement", "", "| Module | Statement | Answer | Placed after | Note |", "|---|---|---|---|---|"]
    for s in statements:
        for p in s["placements"]:
            code = p["module_code"]
            if p["audience"] == "HFW":
                after = section_label(hfw[code]["sections"][p["after_section_number"] - 1])
            else:
                secs = cdd.get(code, {}).get("sections", [])
                i = next((k for k, x in enumerate(secs) if x.get("id") == p["section_id"]), None)
                while i and secs[i - 1]["content_type"] == "TRUE_FALSE":  # several statements in a row
                    i -= 1
                after = section_label(secs[i - 1]) if i else "(CDD content not built yet)"
            out.append(f"| {code} | {s['ref']} {s['statement']} | {'True' if s['answer'] else 'False'} | {after} | {p['note']} |")
    return out


def review_doc(general):
    out = ["# General test and module quizzes: content review", "",
           "Sources: `content/source/Test_Questions_for_CDD_Playbook_version_aa_rev_10.11.26.docx` (25 questions) and "
           "`content/source/Module_Quiz_aa_rev_10.11.26.docx` (27 True/False statements).",
           "Generated by `content/learning_tests/build.py`.", "",
           "## 1. Every change made to the text", "",
           "Only obvious spelling and spacing typos. Question order and option order are as printed.", "",
           "| Where | In the file | In the app |", "|---|---|---|"]
    for where, a, b in CHANGES:
        out.append(f"| {where} | `{a}` | `{b}` |")
    out += ["", "Also: the '(1 Point)' line under each question is a score marker, not question text, and is not shown; "
            "each question is worth 1 point. Trailing spaces were removed.", "",
            "## 2. Answer key for the 25 questions: still needed", "",
            "The test file marks no correct option. The questions are loaded inactive with an empty answer. Fill in "
            "`content/learning_tests/general_test_answer_key_TEMPLATE.csv` or send a list like 1-B, 2-B. The pre-test gate "
            "stays off until the key is loaded and the programme confirms.", "",
            "## 3. Questions that are CDD-specific", "",
            "Every learner (CDD, HFW and others) takes the same 25 questions.", "",
            "| No. | Question | Why |", "|---|---|---|"]
    for q in general:
        why = "the question is about what a CDD does" if q["cdd_specific"] else GENERAL_NOTES.get(q["number"])
        if q["cdd_specific"] or q["number"] in (10, 16):
            out.append(f"| {q['number']} | {q['prompt']} | {why} |")
    out += ["", "## 4. Other notes on the questions", ""]
    out += [f"- Q{n}: {t}" for n, t in sorted(GENERAL_NOTES.items()) if n not in (10, 16)]
    out += ["", "## 5. Module quiz statements", "",
            "- No explanations were supplied for the True/False statements; none were written. Admins can add one per "
            "statement in the module editor.",
            "- 4.2 (house marking) is kept at the end of HFW-06, which does not teach house marking, by programme "
            "decision (2026-11-11); see docs/module-quiz-map.md.",
            "- 6.2 (consent from the head of household) is placed in the IPC modules, which do not teach consent; consent "
            "is in the Safeguarding modules.",
            "- The quiz statements address CDDs ('CDDs should...') also in the HFW modules; kept as written.", ""]
    return out


def main():
    hfw, general, statements = build()
    with open(os.path.join(DOCS, "module-quiz-map.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(quiz_map(hfw, statements)) + "\n")
    with open(os.path.join(DOCS, "test-content-review.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(review_doc(general)) + "\n")
    print(f"{len(general)} General test questions, {len(statements)} statements, "
          f"{sum(len(s['placements']) for s in statements)} placements, {len(CHANGES)} text changes")


if __name__ == "__main__":
    main()
