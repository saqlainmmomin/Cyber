import re
import urllib.parse


def attachment_disposition(filename: str) -> str:
    cleaned = "".join(ch for ch in filename if ch.isprintable())
    fallback = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned).strip("_") or "download"
    encoded = urllib.parse.quote(cleaned or fallback, safe="")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"
