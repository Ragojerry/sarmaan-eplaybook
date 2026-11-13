"""Deactivated accounts (Item 2): one recognisable answer everywhere.

Every request from a deactivated account (login, token refresh, sync and all other
calls) is refused with this message and the header X-Account-Status: deactivated.
The status code stays what older apps already handle (401 for tokens, 403 at
login), so they behave as before; app 0.1.16+ reads the header, signs the person
out and shows its own translated message.
"""
from fastapi import HTTPException, status

ACCOUNT_STATUS_HEADER = "X-Account-Status"
DEACTIVATED_MESSAGE = "Your account has been deactivated. Please contact support."


def deactivated(code: int = status.HTTP_401_UNAUTHORIZED) -> HTTPException:
    headers = {ACCOUNT_STATUS_HEADER: "deactivated"}
    if code == status.HTTP_401_UNAUTHORIZED:
        headers["WWW-Authenticate"] = "Bearer"
    return HTTPException(status_code=code, detail=DEACTIVATED_MESSAGE, headers=headers)
