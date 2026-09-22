"""Short opaque tokens used by the public order survey link."""

from __future__ import annotations

import hashlib
import re
import secrets


_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,25}$")


def generate_token() -> str:
	return secrets.token_urlsafe(15)


def token_digest(token: str) -> str:
	return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def token_is_valid(token: str) -> bool:
	return bool(_TOKEN_PATTERN.fullmatch(str(token or "").strip()))
