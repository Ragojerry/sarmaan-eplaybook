"""App modules built from the flipbook sections (decided split, open_questions.md A1).

Sections are moved by membership only: each entry names the ORIGINAL flipbook
module and its section numbers, so every section keeps the UUID derived from its
original position (uuid5 "hfw|<orig module>|<n>") and every CSV key stays valid.

roles: LearnerRole values. GENERAL modules show to every learner role, so their
learner_roles list stays empty in the app; ROLE_SPECIFIC modules list every role
that needs them (one module, never duplicated).
"""
ALL_ROLES = ["CDD", "HEALTH_WORKER", "LOGISTICIAN", "MONITOR_SUPERVISOR", "OTHER"]

APP_MODULES = [
    {"code": "HFW-01", "audience": "GENERAL", "roles": [],
     "title": "Introduction to Azithromycin (AZM)",
     "description": "What AZM is, who receives it, how often, and how it is delivered.",
     "parts": [("M1", 1, 22)]},
    {"code": "HFW-02", "audience": "GENERAL", "roles": [],
     "title": "Eligibility for AZM",
     "description": "Which children can receive AZM, how to estimate age, and who must not receive it.",
     "parts": [("M2", 1, 33)]},
    {"code": "HFW-03", "audience": "ROLE_SPECIFIC", "roles": ["CDD"],
     "title": "MUAC Nutrition Assessment",
     "description": "Measuring MUAC on children 6-59 months and acting on the result.",
     "parts": [("M2", 34, 44)]},
    {"code": "HFW-04", "audience": "GENERAL", "roles": [],
     "title": "Referral of Children to the Health Facility",
     "description": "When to refer a child, signs of allergy, and the referral steps.",
     "parts": [("M3", 1, 22), ("M3", 32, 32)]},
    {"code": "HFW-05", "audience": "ROLE_SPECIFIC", "roles": ["CDD", "HEALTH_WORKER"],
     "title": "The AZM Referral Form",
     "description": "Completing the CDD and health facility parts of the AZM referral form.",
     "parts": [("M3", 23, 31)]},
    {"code": "HFW-06", "audience": "GENERAL", "roles": [],
     "title": "Giving AZM Safely",
     "description": "Preparing AZM POS, dosing by age and height, giving the dose and observing the child.",
     "parts": [("M4", 1, 23)]},
    {"code": "HFW-07", "audience": "ROLE_SPECIFIC", "roles": ["CDD"],
     "title": "The AZM Child Record Card",
     "description": "What the card records and how to complete each part of it.",
     "parts": [("M4", 24, 35), ("M4", 63, 76)]},
    {"code": "HFW-08", "audience": "ROLE_SPECIFIC", "roles": ["CDD", "MONITOR_SUPERVISOR"],
     "title": "House Marking",
     "description": "Why and how houses are marked, and how to read a house mark.",
     "parts": [("M4", 36, 41)]},
    {"code": "HFW-09", "audience": "ROLE_SPECIFIC", "roles": ["CDD", "HEALTH_WORKER", "MONITOR_SUPERVISOR", "OTHER"],
     "title": "Call-in Data Reporting",
     "description": "Daily call-in data: what it is, who submits and validates it, and how to keep it accurate.",
     "parts": [("M4", 42, 55)]},
    {"code": "HFW-10", "audience": "ROLE_SPECIFIC", "roles": ["CDD", "HEALTH_WORKER", "LOGISTICIAN"],
     "title": "Drug Accountability and Reconciliation",
     "description": "Issuing, counting, reconciling, storing and returning AZM bottles at the health facility.",
     "parts": [("M4", 56, 62)]},
    {"code": "HFW-11", "audience": "ROLE_SPECIFIC", "roles": ["MONITOR_SUPERVISOR", "OTHER"],
     "title": "Cohort Tracking",
     "description": "Following the same children across rounds, and who does what with the data.",
     "parts": [("M4", 77, 84)]},
    {"code": "HFW-12", "audience": "GENERAL", "roles": [],
     "title": "Drug Safety and Side Effects",
     "description": "Side effects, adverse events and serious adverse events, and why they are reported.",
     "parts": [("M5", 1, 6)]},
    {"code": "HFW-13", "audience": "ROLE_SPECIFIC", "roles": ["HEALTH_WORKER"],
     "title": "NAFDAC Reporting and the Role of DSNOs",
     "description": "Reporting suspected ADRs with the Med Safety app and the e-reporting link, and the DSNO role.",
     "parts": [("M5", 7, 27)]},
    {"code": "HFW-14", "audience": "GENERAL", "roles": [],
     "title": "Interpersonal Communication and SBC",
     "description": "Good communication with caregivers and the SBC methods used in the AZM campaign.",
     "parts": [("M6", 1, 11)]},
    {"code": "HFW-15", "audience": "ROLE_SPECIFIC", "roles": ["MONITOR_SUPERVISOR"],
     "title": "Monitoring and Supervision",
     "description": "What supervisors do, the levels of supervision, and the competencies they must show.",
     "parts": [("M7", 1, 10)]},
    {"code": "HFW-16", "audience": "ROLE_SPECIFIC", "roles": ["LOGISTICIAN"],
     "title": "Supply Chain Management",
     "description": "What supply chain management means for AZM and how to manage AZM supplies.",
     "parts": [("M8", 1, 7)]},
    {"code": "HFW-17", "audience": "GENERAL", "roles": [],
     "title": "Safeguarding",
     "description": "Protecting children and vulnerable adults during the AZM campaign, and reporting concerns.",
     "parts": [("M9", 1, 17)]},
]



def learning_order(modules=APP_MODULES):
    """A learner's list: the GENERAL modules first, then the modules of their role
    (changeover decision 1). One global order does this for every role, because a
    learner only sees GENERAL modules plus their own role's. Codes never change."""
    general = [m for m in modules if m["audience"] == "GENERAL"]
    role = [m for m in modules if m["audience"] != "GENERAL"]
    return general + role
