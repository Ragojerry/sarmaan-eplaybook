"""
What a valid app-string translation looks like. Used by in-place editing and by
file import, so both apply exactly the same rules.

Errors block saving:
  - an empty translation;
  - a placeholder the English does not have ({nme} instead of {name}) - the phone
    would show the braces, so it would refuse it and show English anyway;
  - a missing singular form for a plural string, or a singular form for one that is not.
Warnings are shown but do not block (word order differs between languages, and
a translator may legitimately leave a placeholder out):
  - a placeholder of the English that the translation leaves out.
"""
import re

from app.models import AppString

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def placeholders_of(text: str | None) -> set[str]:
    return set(PLACEHOLDER.findall(text or ""))


def check(string: AppString, text: str | None, text_one: str | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = (text or "").strip()
    text_one = (text_one or "").strip()
    allowed = set(string.placeholders or [])

    if not text:
        errors.append("The translation is empty (leave the string untranslated to show English).")
    if string.is_plural and not text_one:
        errors.append("This string has a singular form: translate both forms.")
    if not string.is_plural and text_one:
        errors.append("This string has no singular form; leave the singular empty.")

    for form, value in (("translation", text), ("singular form", text_one)):
        unknown = sorted(placeholders_of(value) - allowed)
        if unknown:
            errors.append(
                f"The {form} uses {', '.join('{' + u + '}' for u in unknown)}, which the English does not have"
                + (f" (allowed: {', '.join('{' + a + '}' for a in sorted(allowed))})." if allowed else ".")
            )
    missing = sorted(allowed - placeholders_of(text))
    if text and missing:
        warnings.append(f"The translation leaves out {', '.join('{' + m + '}' for m in missing)}.")
    return errors, warnings
