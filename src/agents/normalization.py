"""Shared normalization helpers for identity fields.

Phone numbers and IBANs come in many formats — with or without a leading
+, with spaces or dashes, different casing. The agents must compare
user-provided values against seed data robustly, so we strip format
noise before comparison.
"""

from __future__ import annotations

import re


def normalize_phone(phone: str | None) -> str | None:
    """Return only the digits from a phone string, or None if input is empty."""
    if not phone:
        return None
    return re.sub(r"[^\d]", "", phone)


def normalize_iban(iban: str | None) -> str | None:
    """Return uppercase IBAN with all whitespace stripped, or None if empty."""
    if not iban:
        return None
    return re.sub(r"\s", "", iban).upper()
