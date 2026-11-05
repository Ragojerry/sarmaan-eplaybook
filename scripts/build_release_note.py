"""Builds the SARMAAN e-Playbook mobile release note (process flow) workbook."""
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = sys.argv[1]
TEAL = "1F5F5B"
SOFT = "E6F0EE"
SAND = "FBF6EC"
YELLOW = "FFF59D"
F = "Arial"
thin = Side(style="thin", color="C9D3CF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()


def sheet(title, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = title
    ws.sheet_view.showGridLines = False
    return ws


def heading(ws, text, sub=None, width_cols=6):
    ws["A1"] = text
    ws["A1"].font = Font(name=F, size=15, bold=True, color=TEAL)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name=F, size=10, italic=True, color="5A6B66")
        ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=width_cols)
        ws.row_dimensions[2].height = 30


def table(ws, start_row, headers, rows, widths):
    for c, (h, w) in enumerate(zip(headers, widths), start=1):
        cell = ws.cell(row=start_row, column=c, value=h)
        cell.font = Font(name=F, bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", fgColor=TEAL)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = BORDER
        ws.column_dimensions[cell.column_letter].width = w
    for r, row in enumerate(rows, start=start_row + 1):
        for c, v in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = Font(name=F, size=10)
            cell.alignment = WRAP
            cell.border = BORDER
            if (r - start_row) % 2 == 0:
                cell.fill = PatternFill("solid", fgColor=SAND)
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    return start_row + len(rows)


# ---------------------------------------------------------------- Overview
ws = sheet("Overview", first=True)
heading(ws, "SARMAAN e-Playbook mobile app: release note", "Version 0.1.9 (5 November 2026). For the programme team, trainers and field supervisors.", 2)
info = [
    ("App version", "0.1.9 (build 10)"),
    ("Release date", "5 November 2026"),
    ("Release type", "Test release (Android APK)"),
    ("Previous version", "0.1.8 (4 November 2026)"),
    ("Minimum version for the pre-test / post-test flow", "0.1.8. Phones on 0.1.7 or older cannot complete modules that have questions."),
    ("Who should install it", "Every learner and supervisor using the app, especially anyone still on 0.1.8 (it fixes the freeze on completed modules)."),
    ("How to get it", "Download link shared privately by the programme team. Install over the old version: progress and downloaded content are kept."),
    ("File check (SHA-256)", "bb16973a94adee49f37d58202bc8d5291f6d9b1b016614a38d7102fe4bb02b1d"),
    ("Works offline", "Yes. Reading, tests and progress work without internet; results upload automatically when the phone is back online."),
    ("Server", "Already updated (5 November 2026). No action needed from learners."),
]
for i, (k, v) in enumerate(info, start=4):
    a, b = ws.cell(row=i, column=1, value=k), ws.cell(row=i, column=2, value=v)
    a.font, b.font = Font(name=F, bold=True, size=10, color=TEAL), Font(name=F, size=10)
    a.fill = PatternFill("solid", fgColor=SOFT)
    for c in (a, b):
        c.alignment, c.border = WRAP, BORDER
ws.column_dimensions["A"].width = 34
ws.column_dimensions["B"].width = 95
r = 4 + len(info) + 1
ws.cell(row=r, column=1, value="Sheets in this workbook").font = Font(name=F, bold=True, size=11, color=TEAL)
for i, (k, v) in enumerate([
    ("Process flow", "The learner's journey, step by step: what they do, what the app shows, the rule behind it."),
    ("Completion rules", "When a module is completed and the next one unlocks, including the 100% pre-test case."),
    ("What's new", "Changes in 0.1.8 and 0.1.9."),
    ("Learner messages", "What the learner sees in each situation and what it means."),
    ("Support and FAQ", "Common questions and what to tell the learner."),
    ("Field test checklist", "Checks to run on a phone before wider roll-out, with space to record results."),
], start=r + 1):
    ws.cell(row=i, column=1, value=k).font = Font(name=F, bold=True, size=10)
    ws.cell(row=i, column=2, value=v).font = Font(name=F, size=10)

# ---------------------------------------------------------------- Process flow
ws = sheet("Process flow")
heading(ws, "Mobile process flow (learner journey)", "Each module that has questions follows steps 5 to 10. Modules without questions are read and then marked complete with one button.", 7)
flow = [
    (1, "Language and consent", "Chooses a language and accepts the consent text (first launch only).", "Shows the consent text in the chosen language (English if no translation).", "Consent is needed once per phone.", "Yes (after first download)", "Unchanged."),
    (2, "Sign in", "Signs in with the username and password from the programme team.", "Loads the account, including the learner role (CDD, Health Worker, Logistician, Monitor/Supervisor or Others).", "Each person's progress is kept separately, even on a shared phone.", "Needs internet for the first sign-in", "Learner role shown on Home (e.g. CDD TEAM 0041)."),
    (3, "First download", "Waits for the content download.", "Downloads only the modules for the learner's role, plus the general modules, with pictures and quizzes.", "Another role's modules are never sent to the phone.", "Needs internet once", "Role-based content."),
    (4, "Home / Modules list", "Picks a module.", "Lists modules in training order. Each shows its status: Pre-test first, Reading, Post-test ready, Completed or Locked (padlock).", "A module is locked until the one before it is completed.", "Yes", "Status labels and locks."),
    (5, "Pre-test", "Opens an unlocked module and takes the pre-test.", "Blocks the reading until the pre-test is done. After it: shows the score only (not the answers).", "The pre-test is taken once. It is the starting point, not a pass or fail.", "Yes", "New in 0.1.8."),
    (6, "Read the module", "Reads the lessons, plays audio and video, views pictures.", "Shows the pre-test score at the top. Records when the learner reaches the end of the module.", "Reading must be finished before the post-test opens.", "Yes", "New in 0.1.8."),
    (7, "Post-test", "Taps 'Take the post-test' at the end of the module.", "Shows the questions; the button stays grey until reading is finished.", "Retakes are allowed until the module is completed.", "Yes", "New in 0.1.8."),
    (8, "Post-test result", "Reads the result screen.", "Shows the score, a tick or cross for each rule, the correct answers, and what to do next.", "See the 'Completion rules' sheet.", "Yes", "Rule for 100% pre-tests changed in 0.1.9."),
    (9, "Module completed", "Taps 'Next module'.", "Marks the module Completed immediately and unlocks the next module.", "Completion happens on the phone at once, even offline.", "Yes", "No approval step any more (0.1.9)."),
    (10, "Not passed yet", "Taps 'Try again' or 'Re-read the module'.", "Keeps every attempt. Explains which rule was missed.", "No limit on retakes until completed.", "Yes", "Unchanged."),
    (11, "Review a completed module", "Opens a module marked Completed.", "Opens in review mode: lessons, audio, video and pictures work. No post-test button.", "The result and status cannot be changed.", "Yes", "Freeze fixed in 0.1.9."),
    (12, "Sync", "Nothing; it happens automatically when online (or pull down on Home).", "Uploads progress and test results, downloads updates. Uploading twice never counts twice.", "Results taken offline are kept and sent later.", "Needs internet", "Reading progress is sent before test results."),
    (13, "Role change", "Nothing; an administrator changes the learner role.", "At the next sync, swaps to the modules of the new role. Progress is kept.", "Modules of the old role are removed from the phone.", "Needs internet", "New in 0.1.8."),
]
table(ws, 4, ["Step", "Screen", "What the learner does", "What the app does / shows", "Rule", "Offline?", "Change"],
      flow, [6, 22, 38, 52, 40, 18, 28])

# ---------------------------------------------------------------- Rules
ws = sheet("Completion rules")
heading(ws, "When is a module completed?", "These rules are checked on the phone and again on the server, so both always agree.", 5)
rules = [
    ("Normal case", "Post-test is at least 90% AND higher than the pre-test.", "Pre-test 60%, post-test 90%", "Completed. Next module unlocks.", "Scores are compared exactly (e.g. 9/10 is not higher than 18/20)."),
    ("Below the pass mark", "Post-test below 90%.", "Pre-test 60%, post-test 80%", "Not completed. Retake.", ""),
    ("Not higher than the pre-test", "Post-test at least 90% but equal to or lower than the pre-test.", "Pre-test 90%, post-test 90%", "Not completed. Retake (needs more than 90%).", ""),
    ("100% pre-test (auto-approval)", "Post-test at least 90%. No approval step.", "Pre-test 100%, post-test 90%, 95% or 100%", "Completed automatically at once.", "A higher score than 100% is impossible, so the 90% threshold is the only rule for these learners. Changed in 0.1.9."),
    ("100% pre-test, below threshold", "Post-test below 90%.", "Pre-test 100%, post-test 89%", "Not completed. Retake.", "The 90% threshold is a server setting (currently 90)."),
    ("Module without questions", "Learner taps 'Mark as complete'.", "-", "Completed. Next module unlocks.", ""),
    ("Module completed before pre-tests existed", "Stays completed.", "-", "Opens in review mode.", "Applies to modules completed on versions before 0.1.8."),
    ("Locked module", "The module before it is not completed.", "-", "Cannot be opened until the earlier module is completed.", "A module already completed is never locked again."),
]
table(ws, 4, ["Situation", "Rule", "Example", "Result", "Note"], rules, [30, 46, 34, 36, 50])

# ---------------------------------------------------------------- What's new
ws = sheet("What's new")
heading(ws, "What's new", "Most recent first.", 4)
news = [
    ("0.1.9", "5 Nov 2026", "Fix", "Opening a module that was already completed could freeze the app (blank screen, no buttons working) until it was restarted. Completed modules now open in review mode."),
    ("0.1.9", "5 Nov 2026", "Change", "Learners who score 100% on the pre-test are auto-approved: a post-test of 90% or more completes the module at once. The manual approval by an administrator is removed."),
    ("0.1.9", "5 Nov 2026", "Change", "A completed module can no longer be re-tested: the result and status stay as they are."),
    ("0.1.8", "4 Nov 2026", "New", "Pre-test before reading and post-test after reading for every module with questions."),
    ("0.1.8", "4 Nov 2026", "New", "Modules open one after another: the next module unlocks when the previous one is completed."),
    ("0.1.8", "4 Nov 2026", "New", "Learner roles: the app shows general modules plus the modules for the learner's role."),
    ("0.1.8", "4 Nov 2026", "New", "The result screen explains the 90% pass mark, the comparison with the pre-test, and the next step."),
    ("0.1.8", "4 Nov 2026", "Change", "Test results taken offline are kept and uploaded later; reading progress is uploaded first so results are accepted in the right order."),
]
table(ws, 4, ["Version", "Date", "Type", "Description"], news, [10, 14, 10, 110])

# ---------------------------------------------------------------- Messages
ws = sheet("Learner messages")
heading(ws, "Messages the learner sees", "Shown in English; module content follows the chosen language when a translation exists.", 3)
msgs = [
    ("Opens a module for the first time", "Start with the pre-test. Before reading, answer the questions to show what you already know. It is not a pass or fail: it is your starting point.", "Take the pre-test to unlock the reading."),
    ("Opens a locked module", "Locked. Complete [previous module] first. Modules open one after another, when the previous one is completed.", "Finish the earlier module first."),
    ("After the pre-test", "Pre-test done. This is your starting point, not a pass or fail. Now read the module. The post-test opens when you reach the end.", "Read the module to the end."),
    ("After a 100% pre-test", "You already know this module well. Now read the module. When you reach the end, a post-test of 90% or more completes it automatically.", "Read, then take the post-test."),
    ("Post-test button is grey", "Read to the end of the module to open the post-test.", "Scroll to the end of the module."),
    ("Post-test below 90%", "Not yet. You need at least 90%. Look at the answers below, re-read the module, and try the post-test again.", "Re-read and retake."),
    ("Post-test 90% but not higher than the pre-test", "Not yet. You reached 90%, but you need more than your pre-test score. Re-read the parts you missed and try the post-test again.", "Retake and aim higher than the pre-test."),
    ("Post-test passed", "Module complete. The next module is now unlocked.", "Go to the next module."),
    ("Opens a completed module", "Module completed. Your result: pre-test X% · post-test Y%. You can re-read it, play its audio and video and view its pictures; the result stays as it is.", "Review only; nothing to do."),
    ("Tries to open a module of another role", "Not available. This module is not part of the training for your role.", "Ask the supervisor if the learner role looks wrong."),
]
table(ws, 4, ["Situation", "What the app says", "What it means for the learner"], msgs, [36, 90, 42])

# ---------------------------------------------------------------- FAQ
ws = sheet("Support and FAQ")
heading(ws, "Support and frequently asked questions", None, 3)
faq = [
    ("The app froze when I opened a completed module.", "Fixed in 0.1.9. Install 0.1.9 over the old version; progress is kept.", "Learner"),
    ("I can't take the pre-test again.", "The pre-test is taken once on purpose: it is the starting point the post-test is compared with.", "Learner"),
    ("The post-test button is grey.", "Scroll to the very end of the module. The post-test opens after reading.", "Learner"),
    ("I scored 90% but the module did not complete.", "The post-test must also be higher than the pre-test. If the pre-test was 90%, aim for more than 90%. (With a 100% pre-test, 90% is enough.)", "Learner"),
    ("I scored 100% on the pre-test. Do I need approval?", "No. From 0.1.9, a post-test of 90% or more completes the module automatically.", "Learner"),
    ("A module shows a padlock.", "Complete the module before it first. Modules open in order.", "Learner"),
    ("I worked offline. Is my result saved?", "Yes. It is saved on the phone and uploaded automatically when online. Uploading twice never counts twice.", "Learner"),
    ("A learner sees the wrong modules.", "Check the learner role on the admin portal (Users page). The phone updates at its next sync.", "Supervisor"),
    ("Where do I see pre-test and post-test results?", "Admin portal > Reports > Pre/post tests (CSV export available). Click a row for every attempt.", "Supervisor"),
    ("Can a learner change a completed result?", "No. Completed modules are review-only; the score and status are kept.", "Supervisor"),
    ("The learner is on 0.1.7 or older.", "They can read but cannot complete modules with questions. Install 0.1.9.", "Supervisor"),
]
table(ws, 4, ["Question", "Answer", "Who asks"], faq, [48, 95, 14])

# ---------------------------------------------------------------- Checklist
ws = sheet("Field test checklist")
heading(ws, "Field test checklist (0.1.9)", "Legend: fill in the yellow columns (Result: Pass / Fail / Not tested; Tested by; Date; Notes). Row 1 is a worked example.", 8)
checks = [
    ("Example", "Install 0.1.9 over 0.1.8", "Progress and downloaded modules are still there.", "Online"),
    (1, "Sign in as a CDD learner", "Home shows the learner role (e.g. CDD TEAM 0041) and the modules.", "Online"),
    (2, "Open the first module", "Asks for the pre-test before showing the lessons.", "Offline"),
    (3, "Take the pre-test", "Shows the score only, no answers; 'Read the module' button.", "Offline"),
    (4, "Read to the end", "Post-test button becomes active.", "Offline"),
    (5, "Post-test at 80%", "Not completed; explains the 90% pass mark; 'Try again'.", "Offline"),
    (6, "Post-test at 90% or more and higher than the pre-test", "Module complete; next module unlocks.", "Offline"),
    (7, "100% pre-test, then 90% post-test", "Module completes automatically, no approval step.", "Offline"),
    (8, "100% pre-test, then 89% post-test", "Not completed; retake offered.", "Offline"),
    (9, "Open a completed module and tap it several times", "Opens in review mode; no freeze; no post-test button.", "Offline"),
    (10, "Press Back from the completed module", "Returns to the list; all buttons work.", "Offline"),
    (11, "Play audio / video and view pictures in a completed module", "All work; result unchanged.", "Offline"),
    (12, "Open a module after the previous one is not completed", "Shows Locked with the module to finish first.", "Offline"),
    (13, "Go online and sync", "Results appear in admin portal > Reports > Pre/post tests.", "Online"),
]
rows = [list(c) + ["Pass" if c[0] == "Example" else "", "A. Bello" if c[0] == "Example" else "",
                   "05/11/2026" if c[0] == "Example" else "", "Phone: Tecno Spark 10" if c[0] == "Example" else ""] for c in checks]
last = table(ws, 4, ["#", "Check", "Expected result", "Network", "Result", "Tested by", "Date", "Notes"], rows,
             [9, 46, 52, 10, 13, 16, 13, 30])
for r in range(5, last + 1):
    for c in range(5, 9):
        ws.cell(row=r, column=c).fill = PatternFill("solid", fgColor=YELLOW)
    if ws.cell(row=r, column=1).value == "Example":
        for c in range(1, 9):
            ws.cell(row=r, column=c).font = Font(name=F, size=10, italic=True, color="7A7A7A")
dv = DataValidation(type="list", formula1='"Pass,Fail,Not tested"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"E6:E{last}")
s = last + 2
ws.cell(row=s, column=2, value="Summary (excludes the example row)").font = Font(name=F, bold=True, size=10, color=TEAL)
for i, label in enumerate(["Pass", "Fail", "Not tested"]):
    ws.cell(row=s + 1 + i, column=2, value=label).font = Font(name=F, size=10)
    ws.cell(row=s + 1 + i, column=3, value=f'=COUNTIF($E$6:$E${last},"{label}")').font = Font(name=F, size=10)
ws.cell(row=s + 4, column=2, value="Not filled in yet").font = Font(name=F, size=10)
ws.cell(row=s + 4, column=3, value=f'=COUNTBLANK($E$6:$E${last})').font = Font(name=F, size=10)
ws.cell(row=s + 5, column=2, value="Total checks").font = Font(name=F, bold=True, size=10)
ws.cell(row=s + 5, column=3, value=f"=ROWS($E$6:$E${last})").font = Font(name=F, bold=True, size=10)

for w in wb.worksheets:
    w.page_setup.orientation = "landscape"
    w.page_setup.fitToWidth = 1
    w.sheet_properties.pageSetUpPr.fitToPage = True
    w.page_setup.fitToHeight = 0

wb.save(OUT)
print("saved", OUT)
