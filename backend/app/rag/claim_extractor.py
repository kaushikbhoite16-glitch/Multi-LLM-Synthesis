import re
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import logger

FILLER_PATTERNS = [
    r"^here\s+(is|are)\b",
    r"^sure,\s+i\s+can\b",
    r"^certainly\b",
    r"^in\s+conclusion\b",
    r"^to\s+summarize\b",
    r"^overall,\b",
    r"^as\s+an\s+ai\b",
    r"^(i\s+)?hope\s+this\s+helps\b",
    r"^let\s+me\s+know\b",
    r"^\s*$"
]


class ClaimExtractor:
    """
    Extracts atomic factual claims from LLM response text.
    Uses regex syntactic parsing and filtering, with optional LLM decomposition.
    """
    def __init__(self):
        pass

    def extract_claims(self, text: str, max_claims: int = 8) -> List[str]:
        """
        Extracts up to max_claims atomic factual statements from the candidate response.
        """
        if not text or not text.strip():
            return []

        # 1. Clean markdown headers and code blocks
        clean_text = re.sub(r"```[\s\S]*?```", "", text)
        clean_text = re.sub(r"^#+\s*.*$", "", clean_text, flags=re.MULTILINE)

        # 2. Split into candidate sentences
        # Handles periods, question marks, exclamation marks, or bullet points
        raw_sentences = re.split(r"(?<=[.!?])\s+|\n[-*•]\s+|\n\d+\.\s+", clean_text)

        claims = []
        for raw_s in raw_sentences:
            s = raw_s.strip()
            # Clean leading bullets or quotes
            s = re.sub(r"^[-*•\d\.\s\"']+", "", s).strip()
            if not s or len(s.split()) < 4 or len(s) > 300:
                continue

            # Skip questions
            if s.endswith("?"):
                continue

            # Skip conversational greetings and filler
            s_lower = s.lower()
            if any(re.search(pat, s_lower) for pat in FILLER_PATTERNS):
                continue

            claims.append(s)
            if len(claims) >= max_claims:
                break

        if not claims and text.strip():
            # Fallback to first non-empty line
            for line in text.splitlines():
                l = line.strip()
                if len(l.split()) >= 3:
                    claims.append(l[:200])
                    break

        return claims

claim_extractor = ClaimExtractor()
