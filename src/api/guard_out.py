"""GuardOut — output response filter.
 
Checks LLM responses for XSS payloads and PII patterns before
returning them to the user.
"""
 
import logging
import re
from dataclasses import dataclass
 
logger = logging.getLogger("api.guard_out")
 
# --- XSS patterns ---
_XSS_PATTERN = re.compile(r"<\s*/?\s*script", re.IGNORECASE)
 
# --- PII patterns ---
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){16}\b")
 
 
@dataclass
class GuardResult:
    passed: bool
    reason: str | None = None
 
 
def check_output(text: str, *, trace=None) -> GuardResult:
    """Check *text* for XSS tags and PII leaks.
 
    Args:
        text: The LLM response string.
        trace: Optional Langfuse trace to attach a span to.
 
    Returns:
        GuardResult with passed=False if dangerous content is detected.
    """
    reasons: list[str] = []
 
    if _XSS_PATTERN.search(text):
        reasons.append("XSS: <script> tag detected")
 
    if _SSN_PATTERN.search(text):
        reasons.append("PII: SSN pattern detected")
 
    if _CARD_PATTERN.search(text):
        reasons.append("PII: credit card number detected")
 
    passed = len(reasons) == 0
    reason = None if passed else "; ".join(reasons)
 
    if trace is not None:
        try:
            trace.span(
                name="guard_out",
                input={"text": text[:500]},
                output={"passed": passed, "reason": reason},
            )
        except Exception as exc:
            logger.warning("Failed to log guard_out span: %s", exc)
 
    if not passed:
        logger.warning("GuardOut BLOCKED | reason=%s", reason)
    else:
        logger.debug("GuardOut PASSED")
 
    return GuardResult(passed=passed, reason=reason)