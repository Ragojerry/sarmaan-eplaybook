"""Tools repository: link validation and host labels, who may manage it, the audit
trail, role assignment and audience filtering, "changed since" for phones, CSV
import errors, and proof that Tools never touch training (gate, unlock,
completion, time rule, progress, restart, reports, question index).
Links are example.org / well-known hosts with made-up paths only."""
import inspect
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import true

import app.learning.state as state
from app.ai import indexer
from app.auth.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models import AnalyticsEvent, AuditLog, Language, RefreshToken, ToolItem, ToolModule, User, UserModuleProgress
from app.models.enums import AnalyticsEventType, AuditAction, LearnerRole, RoleName, UserStatus
from app.reports.activity import Filters, user_rows
from app.tools.links import LinkError, check_url, host_label
from app.training.restart import restart_training

client = TestClient(app)


def _make_user(db, role, learner_role=None):
    english = db.query(Language).filter_by(code="en").one()
    username = f"test_tools_{role.value.lower()}_{uuid.uuid4().hex[:8]}"
    user = User(username=username, email=f"{username}@sarmaan-eplaybook.app", password_hash=hash_password("TestPass123!"),
                first_name="Test", last_name=role.value, role=role, learner_role=learner_role, language_id=english.id,
                status=UserStatus.ACTIVE)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(user):
    resp = client.post("/auth/login", json={"username": user.username, "password": "TestPass123!"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def users():
    db = SessionLocal()
    existing_modules = {m.id for m in db.query(ToolModule)}
    made = {
        "admin": _make_user(db, RoleName.CONTENT_ADMIN),
        "reader": _make_user(db, RoleName.READ_ONLY),
        "supervisor": _make_user(db, RoleName.SUPERVISOR),
        "cdd": _make_user(db, RoleName.CDD, LearnerRole.CDD),
        "hw": _make_user(db, RoleName.CDD, LearnerRole.HEALTH_WORKER),
        "mon": _make_user(db, RoleName.CDD, LearnerRole.MONITOR_SUPERVISOR),
    }
    yield made
    ids = [u.id for u in made.values()]
    mine = db.query(ToolModule.id).filter(ToolModule.id.notin_(existing_modules) if existing_modules else true())
    db.query(ToolItem).filter(ToolItem.tool_module_id.in_(mine.scalar_subquery())).delete(synchronize_session=False)
    db.query(ToolModule).filter(ToolModule.id.notin_(existing_modules) if existing_modules else true()).delete(synchronize_session=False)
    for model in (RefreshToken, AuditLog, AnalyticsEvent, UserModuleProgress):
        db.query(model).filter(model.user_id.in_(ids)).delete(synchronize_session=False)
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def _module(h, **fields):
    resp = client.post("/tools/modules", headers=h, json={"title": "Field tools", **fields})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _item(h, module_id, **fields):
    body = {"tool_module_id": module_id, "title": "Job aid", "type": "PDF", "url": "https://example.org/job-aid.pdf",
            "category": "Job aids", **fields}
    resp = client.post("/tools/items", headers=h, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _sync(h, since=None):
    resp = client.get("/sync/tools", headers=h, params={"since": since} if since else None)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _audit(user, action):
    db = SessionLocal()
    rows = db.query(AuditLog).filter_by(user_id=user.id, action=action).all()
    db.close()
    return rows


# ---------- links ----------

def test_only_safe_https_links_are_accepted():
    assert check_url(" https://drive.google.com/file/d/abc/view ") == "https://drive.google.com/file/d/abc/view"
    bad = ["http://example.org", "javascript:alert(1)", "JAVASCRIPT:alert(1)", "file:///etc/passwd", "data:text/html,hi",
           "ftp://example.org/x", "example.org/x", "https://", "https://localhost/x", "https://user:pass@example.org/x",
           "https://user@example.org/x", "https://exa mple.org", "https://example.org/a\nb", "https://example.org:99999/",
           "https://" + "a" * 2000 + ".org", "  ", "//example.org/x"]
    for url in bad:
        with pytest.raises(LinkError):
            check_url(url)


def test_hosts_are_labelled_from_the_address_alone():
    assert host_label("https://drive.google.com/file/d/x") == "GOOGLE_DRIVE"
    assert host_label("https://docs.google.com/spreadsheets/d/x") == "GOOGLE_DRIVE"
    assert host_label("https://1drv.ms/w/x") == "ONEDRIVE"
    assert host_label("https://onedrive.live.com/x") == "ONEDRIVE"
    assert host_label("https://contoso.sharepoint.com/sites/x") == "SHAREPOINT"
    assert host_label("https://www.dropbox.com/s/x") == "DROPBOX"
    assert host_label("https://youtu.be/x") == "YOUTUBE"
    assert host_label("https://m.youtube.com/watch?v=x") == "YOUTUBE"
    assert host_label("https://example.org/x") is None
    assert host_label("https://notyoutube.com/x") is None, "a look-alike host is not labelled"
    assert host_label("https://youtube.com.evil.example/x") is None


def test_the_server_never_fetches_links():
    import app.routers.tools as tools_router
    import app.tools.links as links
    for mod in (tools_router, links):
        src = inspect.getsource(mod)
        for fetcher in ("httpx", "requests", "urllib.request", "urlopen", "aiohttp", "socket"):
            assert fetcher not in src, (mod.__name__, fetcher)


# ---------- admin ----------

def test_permissions(users):
    admin, reader, sup, cdd = (_login(users[k]) for k in ("admin", "reader", "supervisor", "cdd"))
    m = _module(admin)
    i = _item(admin, m["id"])
    assert client.get("/tools/modules").status_code == 401
    assert client.get("/tools/items", headers=cdd).status_code == 403
    for h in (reader, sup):
        assert client.get("/tools/modules", headers=h).status_code == 200
        assert client.get("/tools/items", headers=h).status_code == 200
        assert client.get("/tools/opens", headers=h).status_code == 200
        assert client.post("/tools/modules", headers=h, json={"title": "x"}).status_code == 403
        assert client.put(f"/tools/modules/{m['id']}", headers=h, json={"title": "x"}).status_code == 403
        assert client.put(f"/tools/items/{i['id']}/active", headers=h, json={"active": False}).status_code == 403
        assert client.delete(f"/tools/items/{i['id']}", headers=h).status_code == 403
        assert client.post(f"/tools/modules/{m['id']}/items/import", headers=h,
                           files={"file": ("t.csv", b"title,type,url\n", "text/csv")}).status_code == 403
    assert client.get("/sync/tools").status_code == 401


def test_validation_through_the_api(users):
    admin = _login(users["admin"])
    m = _module(admin)
    for url, msg in (("http://example.org", "https://"), ("javascript:alert(1)", "https://"),
                     ("https://u:p@example.org", "user name or password")):
        resp = client.post("/tools/items", headers=admin, json={"tool_module_id": m["id"], "title": "x", "type": "PDF", "url": url})
        assert resp.status_code == 422 and msg in resp.json()["detail"], resp.text
    assert client.post("/tools/items", headers=admin, json={"tool_module_id": m["id"], "title": "x", "type": "ZIP",
                                                             "url": "https://example.org"}).status_code == 422
    assert client.post("/tools/modules", headers=admin, json={"title": "x", "audience": "ROLE_SPECIFIC"}).status_code == 422
    assert client.post("/tools/items", headers=admin, json={"tool_module_id": str(uuid.uuid4()), "title": "x", "type": "PDF",
                                                             "url": "https://example.org"}).status_code == 404


def test_every_change_is_audited_and_duplicates_are_flagged(users):
    admin_user = users["admin"]
    admin = _login(admin_user)
    m = _module(admin)
    m2 = _module(admin, title="Supervisor tools", audience="ROLE_SPECIFIC", learner_roles=["MONITOR_SUPERVISOR"])
    a = _item(admin, m["id"], url="https://drive.google.com/file/d/one/view")
    b = _item(admin, m["id"], title="Same file", url="https://DRIVE.google.com/file/d/one/view/")
    assert a["host"] == "GOOGLE_DRIVE"
    assert [d["id"] for d in b["duplicates"]] == [a["id"]], "duplicate link warning"
    assert len(_audit(admin_user, AuditAction.TOOL_CREATE)) == 4

    upd = client.put(f"/tools/items/{a['id']}", headers=admin, json={"tool_module_id": m["id"], "title": "Job aid v2", "type": "PDF",
                                                                     "url": a["url"], "last_reviewed": "2026-11-01"})
    assert upd.status_code == 200 and upd.json()["last_reviewed"] == "2026-11-01"
    (log,) = _audit(admin_user, AuditAction.TOOL_UPDATE)
    assert log.details["before"]["title"] == "Job aid" and log.details["after"]["title"] == "Job aid v2"

    assert client.post(f"/tools/modules/{m['id']}/items/reorder", headers=admin, json={"ids": [b["id"], a["id"]]}).status_code == 200
    ids = [x["id"] for x in client.get("/tools/modules", headers=admin).json()]
    assert client.post("/tools/modules/reorder", headers=admin, json={"ids": list(reversed(ids))}).status_code == 200
    assert len(_audit(admin_user, AuditAction.TOOL_REORDER)) == 2

    client.put(f"/tools/items/{a['id']}/active", headers=admin, json={"active": False})
    client.put(f"/tools/modules/{m2['id']}/active", headers=admin, json={"active": False})
    client.put(f"/tools/modules/{m2['id']}/active", headers=admin, json={"active": True})
    assert len(_audit(admin_user, AuditAction.TOOL_DEACTIVATE)) == 2
    assert len(_audit(admin_user, AuditAction.TOOL_ACTIVATE)) == 1

    assert client.delete(f"/tools/items/{b['id']}", headers=admin).status_code == 204
    assert client.delete(f"/tools/modules/{m['id']}", headers=admin).status_code == 204
    deletes = _audit(admin_user, AuditAction.TOOL_DELETE)
    assert {d.entity_type for d in deletes} == {"tool_item", "tool_module"}
    assert a["id"] in next(d for d in deletes if d.entity_type == "tool_module").details["items_deleted"]
    assert m["id"] not in [x["id"] for x in client.get("/tools/modules", headers=admin).json()]
    assert a["id"] not in [x["id"] for x in client.get("/tools/items", headers=admin).json()]


def test_csv_import_reports_every_bad_row_and_imports_nothing(users):
    admin_user = users["admin"]
    admin = _login(admin_user)
    m = _module(admin)

    def upload(text):
        return client.post(f"/tools/modules/{m['id']}/items/import", headers=admin,
                           files={"file": ("tools.csv", text.encode("utf-8"), "text/csv")})

    bad = ("title,description,type,url,category\n"
           "Good,ok,PDF,https://example.org/a.pdf,Forms\n"
           ",no title,PDF,https://example.org/b.pdf,Forms\n"
           "Insecure,,WEBSITE,http://example.org,\n"
           "Wrong type,,ZIP,https://example.org/c,\n"
           "Script,,WEBSITE,javascript:alert(1),\n")
    resp = upload(bad)
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "Nothing was imported" in detail["message"]
    assert [e["row"] for e in detail["errors"]] == [3, 4, 5, 6]
    assert "title is empty" in detail["errors"][0]["error"] and "https://" in detail["errors"][1]["error"]
    assert "ZIP" in detail["errors"][2]["error"]
    assert m["id"] not in {x["tool_module_id"] for x in client.get("/tools/items", headers=admin).json()}

    assert upload("name,link\nx,y\n").json()["detail"]["message"].startswith("Missing column(s): title, type, url")
    assert upload("title,type,url\n").json()["detail"]["message"] == "The file has no rows to import."

    good = ("﻿title,description,type,url,category,languages\n"
            "Referral form,Paper form,form,https://docs.google.com/forms/d/x,Forms,English\n"
            "Dosing chart,,Spreadsheet,https://example.org/dose.xlsx,Job aids,\n")
    resp = upload(good)
    assert resp.status_code == 200 and resp.json()["created"] == 2, resp.text
    items = [x for x in client.get("/tools/items", headers=admin).json() if x["tool_module_id"] == m["id"]]
    assert [(x["title"], x["type"], x["host"], x["display_order"]) for x in items] == [
        ("Referral form", "FORM", "GOOGLE_DRIVE", 0), ("Dosing chart", "SPREADSHEET", None, 1)]
    (log,) = _audit(admin_user, AuditAction.TOOL_IMPORT)
    assert len(log.details["created"]) == 2


# ---------- phones ----------

def test_role_assignment_and_item_audience(users):
    admin = _login(users["admin"])
    general = _module(admin, title="General tools")
    sup_only = _module(admin, title="Supervisor tools", audience="ROLE_SPECIFIC", learner_roles=["MONITOR_SUPERVISOR"])
    off = _module(admin, title="Inactive tools", is_active=False)
    everyone = _item(admin, general["id"], title="Everyone")
    hw_only = _item(admin, general["id"], title="Health workers", audience=["HEALTH_WORKER"])
    hidden = _item(admin, general["id"], title="Inactive", is_active=False)
    sup_item = _item(admin, sup_only["id"], title="Supervision checklist")
    off_item = _item(admin, off["id"], title="In an inactive module")
    mine = {everyone["id"], hw_only["id"], hidden["id"], sup_item["id"], off_item["id"]}

    def seen(key):
        data = _sync(_login(users[key]))
        return {m["id"] for m in data["modules"]}, {i["id"] for i in data["items"]} & mine

    mods, items = seen("cdd")
    assert general["id"] in mods and sup_only["id"] not in mods and off["id"] not in mods and items == {everyone["id"]}
    mods, items = seen("hw")
    assert general["id"] in mods and sup_only["id"] not in mods and items == {everyone["id"], hw_only["id"]}
    mods, items = seen("mon")
    assert sup_only["id"] in mods and items == {everyone["id"], sup_item["id"]}
    mods, items = seen("supervisor")
    assert {general["id"], sup_only["id"]} <= mods and off["id"] not in mods
    assert items == {everyone["id"], hw_only["id"], sup_item["id"]}, "staff see every active item"
    row = next(i for i in _sync(_login(users["hw"]))["items"] if i["id"] == hw_only["id"])
    assert set(row) == {"id", "tool_module_id", "title", "description", "type", "url", "host", "category", "languages", "display_order"}


def test_changed_since(users):
    admin = _login(users["admin"])
    hw = _login(users["hw"])
    m = _module(admin, title="Changes")
    other = _module(admin, title="Will be switched off")
    keep = _item(admin, m["id"], title="Unchanged")
    edit = _item(admin, m["id"], title="Edited")
    gone = _item(admin, m["id"], title="Deleted")
    via_module = _item(admin, other["id"], title="Module switched off")
    first = _sync(hw)
    assert first["full"] and {keep["id"], edit["id"], gone["id"], via_module["id"]} <= {i["id"] for i in first["items"]}

    db = SessionLocal()
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db.query(ToolItem).filter(ToolItem.tool_module_id.in_([uuid.UUID(m["id"]), uuid.UUID(other["id"])])).update(
        {ToolItem.updated_at: old}, synchronize_session=False)
    db.query(ToolModule).filter(ToolModule.id.in_([uuid.UUID(m["id"]), uuid.UUID(other["id"])])).update(
        {ToolModule.updated_at: old}, synchronize_session=False)
    db.commit()
    db.close()
    since = datetime(2020, 6, 1, tzinfo=timezone.utc).isoformat()

    client.put(f"/tools/items/{edit['id']}", headers=admin, json={"tool_module_id": m["id"], "title": "Edited again", "type": "PDF",
                                                                  "url": "https://example.org/job-aid.pdf"})
    client.delete(f"/tools/items/{gone['id']}", headers=admin)
    client.put(f"/tools/modules/{other['id']}/active", headers=admin, json={"active": False})
    changes = _sync(hw, since)
    assert changes["full"] is False
    ids = {i["id"] for i in changes["items"]}
    assert edit["id"] in ids and keep["id"] not in ids
    assert {gone["id"], via_module["id"]} <= set(changes["removed"]) and keep["id"] not in changes["removed"]
    assert other["id"] not in {x["id"] for x in changes["modules"]}


def test_most_opened_counts_only(users):
    admin = _login(users["admin"])
    m = _module(admin)
    a = _item(admin, m["id"], title="Popular")
    b = _item(admin, m["id"], title="Less popular", url="https://example.org/b")
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    for n, item in ((3, a), (1, b)):
        for _ in range(n):
            db.add(AnalyticsEvent(event_type=AnalyticsEventType.TOOL_OPEN, user_id=users["hw"].id, device_id="dev-tools",
                                  payload={"item_id": item["id"]}, occurred_at=now))
    db.commit()
    db.close()
    old = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)
    db = SessionLocal()
    db.add(AnalyticsEvent(event_type=AnalyticsEventType.TOOL_OPEN, user_id=users["hw"].id, device_id="dev-tools",
                          payload={"item_id": b["id"]}, occurred_at=old))
    db.commit()
    db.close()

    def counts(**params):
        data = client.get("/tools/opens", headers=admin, params=params).json()
        assert all(set(r) == {"item_id", "title", "deleted", "opens"} for r in data["items"]), "no people or devices"
        return data, [(r["title"], r["opens"]) for r in data["items"] if r["item_id"] in (a["id"], b["id"])]

    data, mine = counts()  # default: the last 90 days
    assert mine == [("Popular", 3), ("Less popular", 1)] and data["date_from"] and data["all_time"] is False
    assert counts(all_time="true")[1] == [("Popular", 3), ("Less popular", 2)]
    assert counts(date_from="2026-01-10", date_to="2026-01-10")[1] == [("Less popular", 1)], "both ends inclusive"
    assert counts(date_from="2026-01-11", date_to="2026-01-31")[1] == []
    today = now.date().isoformat()
    assert counts(date_from=today, date_to=today)[1] == [("Popular", 3), ("Less popular", 1)]
    assert client.get("/tools/opens", headers=admin, params={"date_from": "2026-02-01", "date_to": "2026-01-01"}).status_code == 422


# ---------- training is untouched ----------

def _training(db, user):
    """Everything training decides for this person, with the real settings and with the General test on."""
    out = []
    real = state.training_settings
    for active in (None, True):
        if active:
            state.training_settings = lambda d: replace(real(d), general_test_active=True)
        try:
            states, g = state.learning_overview(db, user)
        finally:
            state.training_settings = real
        out.append(([(s.module.module_code, s.status, s.unlocked, s.lock_reason, s.completed, s.quiz_passed, s.time_met,
                      s.seconds_spent, s.completion_problem()) for s in states],
                    (g.modules_total, g.modules_completed, g.all_modules_completed, g.gate_open, g.post_unlocked)))
    return out


def test_tools_never_change_training_results(users):
    admin = _login(users["admin"])
    heads = {k: _login(users[k]) for k in ("cdd", "hw", "mon")}  # signed in first: a login is recorded in the report
    db = SessionLocal()
    learners = [db.get(User, users[k].id) for k in ("cdd", "hw", "mon")]
    before = {u.username: _training(db, u) for u in learners}
    report_before = [r for r in user_rows(db, Filters()) if r.get("username") in before]
    db.close()

    general = _module(admin, title="General tools")
    sup = _module(admin, title="Supervisor tools", audience="ROLE_SPECIFIC", learner_roles=["MONITOR_SUPERVISOR"])
    a = _item(admin, general["id"])
    _item(admin, sup["id"], title="Checklist", url="https://example.org/check")
    for key in ("cdd", "hw", "mon"):
        assert _sync(heads[key])["items"], "every learner has tools assigned"

    db = SessionLocal()
    later = datetime.now(timezone.utc) + timedelta(minutes=1)
    for u in learners:  # opening tools (and tapping the Support deck) is not training activity
        db.add(AnalyticsEvent(event_type=AnalyticsEventType.TOOL_OPEN, user_id=u.id, device_id="dev-tools",
                              payload={"item_id": a["id"]}, occurred_at=later))
        db.add(AnalyticsEvent(event_type=AnalyticsEventType.SUPPORT_CONTACT_TAP, user_id=u.id, device_id="dev-tools",
                              payload={"contact_type": "PHONE"}, occurred_at=later))
    db.commit()
    learners = [db.get(User, u.id) for u in learners]
    assert {u.username: _training(db, u) for u in learners} == before, "pre-test gate, unlock, completion, time rule, progress"
    report_after = [r for r in user_rows(db, Filters()) if r.get("username") in before]
    changed = {k for b, a in zip(report_before, report_after) for k in b if b[k] != a.get(k)}
    assert len(report_after) == len(report_before) and not changed, f"training report fields changed: {changed}"
    db.close()

    # A restart replaces the training attempt and leaves every Tools module and link as it was.
    db = SessionLocal()
    tools_before = sorted((str(i.id), i.is_active, i.updated_at) for i in db.query(ToolItem))
    hw = db.get(User, users["hw"].id)
    assert restart_training(db, hw, datetime.now(timezone.utc), hw, via="test")
    db.commit()
    assert sorted((str(i.id), i.is_active, i.updated_at) for i in db.query(ToolItem)) == tools_before
    db.close()
    assert a["id"] in {i["id"] for i in _sync(heads["hw"])["items"]}, "still assigned after a restart"


def test_tools_are_never_in_the_question_index():
    src = inspect.getsource(indexer)
    assert "Tool" not in src and "tool_items" not in src, "the index is built from training modules only"
