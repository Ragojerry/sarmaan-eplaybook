"""Every content figure in FLIPBOOK HFW, read page by page from the renders.

box: preview pixels (page rendered 1100 px wide). src: "render" or an embedded
file from hfw/embedded/. kind decides the output format and size limit.
"""

# (file stem, page, module, source, box, kind, image type, nearby heading)
FIGURES = [
    ("m1_p01_01", 1, "M1", "render", (752, 365, 1035, 600), "diagram", "illustration", "Azithromycin Drug Administration Training Flipbook (title page)"),
    ("m1_p05_01", 5, "M1", "p05_e00.png", (0, 0, 606, 777), "photo", "cover", "Module 1: Introduction to Azithromycin (AZM) Drug Administration"),
    ("m2_p09_01", 9, "M2", "p09_e00.png", (0, 0, 606, 777), "photo", "cover", "Module 2: Determination of Eligibility for Azithromycin (AZM) Drug Administration"),
    ("m2_p12_01", 12, "M2", "render", (118, 150, 1018, 385), "diagram", "icon strip", "How to determine child's age for AZM drug administration - Children 1 to 11 months"),
    ("m2_p12_02", 12, "M2", "render", (228, 415, 910, 648), "diagram", "icon strip", "How to determine child's age for AZM drug administration - Child 12 to 59 months"),
    ("m2_p14_01", 14, "M2", "render", (190, 200, 925, 330), "diagram", "icon strip", "Determination of eligibility for Azithromycin (AZM) - Eligible for AZM"),
    ("m2_p14_02", 14, "M2", "render", (148, 392, 958, 565), "diagram", "icon strip", "Determination of eligibility for Azithromycin (AZM) - NOT Eligible for AZM"),
    ("m2_p16_01", 16, "M2", "render", (130, 195, 1012, 668), "form", "diagram", "Summary of child eligibility for AZM"),
    ("m2_p18_01", 18, "M2", "p18_e00.png", None, "form", "diagram", "2. MUAC/Nutrition Assessment (Children 6-59 months)"),
    ("m2_p19_01", 19, "M2", "p19_e00.png", None, "diagram", "illustration", "MUAC Assessment: Right and Wrong"),
    ("m2_p20_01", 20, "M2", "render", (118, 100, 446, 620), "photo", "photo", "A CDD taking MUAC reading of a child within the age group 6-59 months"),
    ("m2_p20_02", 20, "M2", "render", (455, 262, 1022, 418), "diagram", "illustration", "MUAC Tape"),
    ("m3_p21_01", 21, "M3", "p21_e00.png", (0, 0, 606, 777), "photo", "cover", "Module 3: Steps for referral of children to health facility"),
    ("m3_p23_01", 23, "M3", "render", (765, 163, 1058, 415), "diagram", "illustration", "When to refer a sick child"),
    ("m3_p23_02", 23, "M3", "render", (780, 418, 1058, 582), "diagram", "illustration", "When to refer a sick child"),
    ("m3_p24_01", 24, "M3", "p24_e01.png", None, "diagram", "icon strip", "When to refer children to health facility - possible allergy to AZM"),
    ("m3_p24_02", 24, "M3", "p24_e00.png", None, "diagram", "icon strip", "When to refer children to health facility - reasons for exclusion"),
    ("m3_p25_01", 25, "M3", "render", (205, 495, 990, 668), "diagram", "diagram", "Referral steps during AZM campaign"),
    ("m3_p26_01", 26, "M3", "render", (106, 203, 380, 645), "form", "form", "Completing the top section of the AZM referral form"),
    ("m4_p28_01", 28, "M4", "render", (103, 0, 626, 692), "photo", "cover", "Module 4: Azithromycin Drug Administration and Recording"),
    ("m4_p30_01", 30, "M4", "render", (108, 465, 1012, 632), "diagram", "icon strip", "Azithromycin Powdered Oral Suspension (AZM POS)"),
    ("m4_p34_01", 34, "M4", "render", (665, 140, 1047, 650), "form", "form", "Completing the child record card"),
    ("m4_p35_01", 35, "M4", "render", (620, 150, 1052, 618), "photo", "photo", "Housemarking guide during AZM MDA"),
    ("m4_p39_01", 39, "M4", "render", (568, 192, 1068, 690), "photo", "photo", "Introduction to call-in data in AZM MDA"),
    ("m4_p41_01", 41, "M4", "render", (622, 218, 1007, 535), "photo", "photo", "Introduction to call-in data in AZM MDA - how call-in data is used"),
    ("m4_p43_01", 43, "M4", "render", (578, 140, 1081, 563), "photo", "cover", "Section 3: Procedures for azithromycin drug accountability and reconciliation in the health facility"),
    ("m4_p49_01", 49, "M4", "p49_e02.png", None, "form", "form", "Steps for completing the child record card during AZM MDA"),
    ("m4_p55_01", 55, "M4", "render", (228, 185, 746, 648), "diagram", "cover", "AZM cohort tracking"),
    ("m4_p60_01", 60, "M4", "render", (128, 72, 1042, 690), "diagram", "diagram", "Cohort tracking responsibility flow"),
    ("m5_p61_01", 61, "M5", "render", (44, 155, 583, 625), "diagram", "cover", "Module 5: Pharmacovigilance - reporting of side effects and adverse effects"),
    ("m5_p64_01", 64, "M5", "p64_e00.png", None, "form", "screenshot", "NAFDAC Med Safety App - practical demo"),
    ("m5_p66_01", 66, "M5", "render", (566, 303, 980, 546), "photo", "photo", "Steps for completing the NAFDAC e-reporting link"),
    ("m6_p73_01", 73, "M6", "p73_e01.png", None, "photo", "cover", "Module 6: Interpersonal communication and Social behaviour (SBC)"),
    ("m7_p77_01", 77, "M7", "p77_e00.png", (0, 0, 606, 777), "photo", "cover", "Module 7: Monitoring and supervision during AZM campaign"),
    ("m8_p81_01", 81, "M8", "p81_e00.png", (0, 0, 606, 777), "photo", "cover", "Module 8: Supply chain management during AZM MDA campaign"),
    ("m9_p84_01", 84, "M9", "render", (0, 72, 581, 692), "photo", "cover", "Module 9: Safeguarding"),
    ("m9_p88_01", 88, "M9", "render", (141, 186, 564, 426), "photo", "photo", "Safeguarding - avoid taking pictures without consent"),
    ("m9_p88_02", 88, "M9", "render", (631, 183, 1010, 424), "photo", "photo", "Safeguarding - avoid taking pictures without consent"),
    ("m9_p88_03", 88, "M9", "render", (402, 435, 760, 638), "photo", "photo", "Safeguarding - avoid bribery and corrupt practices"),
]

LOGOS = [
    ("fmoh_federal_ministry_of_health", 1, "render", (120, 80, 356, 166)),
    ("nphcda", 1, "render", (352, 80, 458, 168)),
    ("sarmaan_ii_project", 1, "render", (462, 92, 621, 153)),
    ("nimr", 1, "render", (627, 80, 713, 158)),
    ("gates_foundation", 1, "render", (716, 98, 841, 146)),
    ("malaria_consortium", 1, "render", (845, 88, 996, 159)),
    ("nafdac_med_safety_app_icon", 64, "p64_e01.png", None),
]

# embedded covers whose raster has the page's teal/black side bar baked into the right edge:
# keep this fraction of the width (a crop, not a retouch)
TRIM_RIGHT = {"m1_p05_01": 0.952, "m2_p09_01": 0.952, "m3_p21_01": 0.952}
