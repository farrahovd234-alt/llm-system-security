"""GuardIn — input prompt filter.
 
Checks incoming user prompts for known injection stop-words.
Blocks the request if any are found.
"""
 
import logging
from dataclasses import dataclass
 
logger = logging.getLogger("api.guard_in")
 
STOP_WORDS: list[str] = ["ignore", "admin", "system"]
 
 
@dataclass
class GuardResult:
    passed: bool
    reason: str | None = None
 
 
def check_input(text: str, *, trace=None) -> GuardResult:
    """Check *text* against stop-word list (case-insensitive substring match).
 
    Args:
        text: The raw user prompt.
        trace: Optional Langfuse trace to attach a span to.
 
    Returns:
        GuardResult with passed=False if a stop-word is detected.
    """
    text_lower = text.lower()
 
    matched: list[str] = [w for w in STOP_WORDS if w in text_lower]
 
    passed = len(matched) == 0
    reason = None if passed else f"Blocked stop-words: {', '.join(matched)}"
 
    if trace is not None:
        try:
            trace.span(
                name="guard_in",
                input={"text": text},
                output={"passed": passed, "reason": reason},
            )
        except Exception as exc:
            logger.warning("Failed to log guard_in span: %s", exc)
 
    if not passed:
        logger.warning("GuardIn BLOCKED | reason=%s | input=%r", reason, text[:200])
    else:
        logger.debug("GuardIn PASSED | input=%r", text[:200])
 
    return GuardResult(passed=passed, reason=reason)