"""Tiny DSL for the HFW flipbook content. Each call appends one app section to the
current module. Tags: general, cdd, health_worker, logistician, supervisor_monitor, other."""

MODULES = []
_cur = None
_ctx = {"tags": ("general",), "evidence": "", "inferred": True}


def module(code, title, description):
    global _cur
    _cur = {"code": code, "title": title, "description": description, "sections": []}
    MODULES.append(_cur)


def audience(*tags, evidence="", inferred=True):
    """Sets the audience for the sections that follow."""
    _ctx.update(tags=tags, evidence=evidence, inferred=inferred)


def _add(kind, pages, content, title=None, **extra):
    s = {"type": kind, "pages": pages if isinstance(pages, (list, tuple)) else [pages],
         "content": content, "title": title, "tags": list(_ctx["tags"]),
         "evidence": _ctx["evidence"], "inferred": _ctx["inferred"]}
    s.update(extra)
    _cur["sections"].append(s)


def H(text, p):
    _add("HEADING", p, {"text": text})


def T(text, p, title=None):
    _add("TEXT", p, {"text": text}, title)


def L(items, p, title=None, transcribed=False):
    _add("LIST", p, {"items": list(items)}, title, transcribed=transcribed)


def TB(headers, rows, p, title=None, transcribed=False):
    _add("TABLE", p, {"headers": list(headers), "rows": [list(r) for r in rows]}, title, transcribed=transcribed)


def C(heading, text, p):
    _add("CALLOUT", p, {"heading": heading, "text": text}, heading)


def W(heading, text, p):
    _add("WARNING", p, {"heading": heading, "text": text}, heading)


def I(file, caption, alt, p, flag=None):
    _add("IMAGE", p, {"image_file": file, "caption": caption, "alt": alt}, flag=flag)
