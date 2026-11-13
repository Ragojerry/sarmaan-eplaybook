"""Checks a Support contact's value for its type before it is saved.

PHONE, SMS, WHATSAPP  international format: a leading + and 8 to 15 digits
                      (spaces are removed first, nothing else is accepted)
EMAIL                 one address, name@domain.tld
LINK                  an https:// address with a host

Anything else is rejected with a message the admin portal shows as is.
"""
import re
from urllib.parse import urlsplit

from app.models.enums import SupportContactType

NUMBER_TYPES = (SupportContactType.PHONE, SupportContactType.SMS, SupportContactType.WHATSAPP)
_NUMBER = re.compile(r"^\+[1-9]\d{7,14}$")
_EMAIL = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$")


class ContactValueError(ValueError):
    pass


def normalise_value(contact_type: SupportContactType, raw: str) -> str:
    """The value to store, or ContactValueError explaining what is wrong."""
    value = (raw or "").strip()
    if not value:
        raise ContactValueError("Enter a value for this contact.")
    if contact_type in NUMBER_TYPES:
        number = value.replace(" ", "")
        if not _NUMBER.match(number):
            raise ContactValueError(
                "Enter the number in international format: a + followed by the country code and number, "
                "digits only (for example +234 800 000 0000).")
        return number
    if contact_type == SupportContactType.EMAIL:
        if len(value) > 254 or not _EMAIL.match(value) or ".." in value:
            raise ContactValueError("Enter a valid email address (for example name@example.org).")
        return value
    if contact_type == SupportContactType.LINK:
        if any(c.isspace() for c in value) or len(value) > 500:
            raise ContactValueError("Enter a single web address without spaces.")
        parts = urlsplit(value)
        if parts.scheme.lower() != "https" or not parts.hostname or "." not in parts.hostname:
            raise ContactValueError("Links must start with https:// and include a website address.")
        return value
    raise ContactValueError("Unknown contact type.")
