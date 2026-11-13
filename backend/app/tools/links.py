"""Checks a Tools repository link and labels its host, from the text alone.

The server never opens these addresses (no link checking: fetching an address
an admin typed would let the server be pointed at internal systems). Rules:
  - https only (http, javascript:, file:, data:, ftp: ... are rejected);
  - at most 2000 characters, no spaces or control characters;
  - a real host name with a dot (no "localhost");
  - no user name or password inside the address (https://user:pass@host).
"""
from urllib.parse import urlsplit

MAX_URL = 2000

# host suffix -> label the app shows an icon for
_HOSTS = (
    (("drive.google.com", "docs.google.com"), "GOOGLE_DRIVE"),
    (("onedrive.live.com", "1drv.ms"), "ONEDRIVE"),
    (("sharepoint.com",), "SHAREPOINT"),
    (("dropbox.com", "dropboxusercontent.com"), "DROPBOX"),
    (("youtube.com", "youtu.be"), "YOUTUBE"),
)


class LinkError(ValueError):
    pass


def check_url(raw: str) -> str:
    """The address to store, or LinkError with a message for the admin."""
    url = (raw or "").strip()
    if not url:
        raise LinkError("Enter the link.")
    if len(url) > MAX_URL:
        raise LinkError(f"The link is too long (more than {MAX_URL} characters).")
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        raise LinkError("The link must not contain spaces.")
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port_ok = parts.port is None or parts.port > 0  # raises on a bad port
    except ValueError:
        raise LinkError("This is not a valid web address.")
    if parts.scheme.lower() != "https":
        raise LinkError("Only https:// links are allowed.")
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        raise LinkError("Remove the user name or password from the link.")
    if not host or "." not in host or host.endswith(".") or not port_ok:
        raise LinkError("The link needs a website address, for example https://drive.google.com/...")
    return url


def host_label(url: str) -> str | None:
    """GOOGLE_DRIVE, ONEDRIVE, SHAREPOINT, DROPBOX, YOUTUBE or None."""
    host = (urlsplit(url).hostname or "").lower()
    for suffixes, label in _HOSTS:
        if any(host == s or host.endswith("." + s) for s in suffixes):
            return label
    return None


def same_link(url: str) -> str:
    """For the duplicate warning: case-insensitive host, no trailing slash or #fragment."""
    p = urlsplit(url)
    return f"{(p.hostname or '').lower()}{p.path.rstrip('/')}{'?' + p.query if p.query else ''}"
