"""Gov-of-India topic gate (Stage1). Only matching posts enter the router."""
from __future__ import annotations

import re

# Short acronyms match on word boundaries only (avoids "eci" in "special").
ACRONYMS = ("pib", "eci", "rbi", "isro", "caa", "upi", "pmo")
PHRASES = (
    "pmo india", "president of india", "election commission",
    "supreme court of india", "indian army", "mea india",
    "aadhaar", "ayushman", "pm-kisan", "agniveer",
    "government of india", "govt of india", "bharat sarkar",
    "delhi police", "mumbai police", "parliament", "lok sabha",
    "rajya sabha", "ministry of", "home minister", "prime minister",
    "chief minister", "ias", "ips", "protest", "viral video",
    "fake news", "fact check", "bjp", "aap",
)

MIN_TEXT_LEN = 4


def mentions_gov(text: str) -> bool:
    lowered = (text or "").lower()
    if len(lowered.strip()) < MIN_TEXT_LEN:
        return False
    if any(phrase in lowered for phrase in PHRASES):
        return True
    return any(re.search(rf"\b{re.escape(a)}\b", lowered) for a in ACRONYMS)
