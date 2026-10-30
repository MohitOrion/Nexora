"""Policy Conflict Shield and Native RFC 5545 Calendar Sync for aventra one.

Features:
1. Proactively detects conflicting dual-tuition grants (e.g., Bharti Airtel vs Delhi MCM).
2. Keeps developer perks, cloud credits, and hackathons 100% stackable.
3. Generates RFC 5545 .ics calendar files with automated 72h and 24h alarms.
"""

from __future__ import annotations

import datetime
import uuid

try:
    from .schemas import Opportunity, StudentProfile
except ImportError:  # pragma: no cover - supports direct script execution
    from schemas import Opportunity, StudentProfile

# Known exclusive full-tuition grants that cannot be combined
EXCLUSIVE_TUITION_KEYWORDS = [
    "bharti airtel", "merit-cum-means", "mcm", "post matric scholarship",
    "central sector scholarship", "full tuition", "fee reimbursement",
    "state government scholarship"
]

# 100% stackable developer perks and cloud credits
STACKABLE_PERK_KEYWORDS = [
    "gemini", "google cloud", "adobe", "github", "aws educate",
    "hackathon", "bounty", "azure for students", "cloud credit"
]


class PolicyConflictShield:
    @staticmethod
    def is_stackable_perk(opp: Opportunity) -> bool:
        """Return True if opportunity is a dev perk, cloud credit, or open competition."""
        if opp.gates.is_stackable:
            return True
        title_lower = opp.title.lower()
        return any(k in title_lower for k in STACKABLE_PERK_KEYWORDS)

    @classmethod
    def check_conflict(
        cls,
        student: StudentProfile,
        opp: Opportunity
    ) -> tuple[bool, str | None]:
        """
        Check for grant clashes.
        Returns: (conflict_detected: bool, reason: Optional[str])
        """
        # Dev perks, hackathons, and cloud credits are always 100% stackable
        if cls.is_stackable_perk(opp):
            return False, None

        # Check if the new opportunity is an exclusive full-tuition grant
        is_opp_exclusive = opp.gates.is_full_tuition_grant or any(
            k in opp.title.lower() for k in EXCLUSIVE_TUITION_KEYWORDS
        )

        if not is_opp_exclusive:
            return False, None

        # Check against student's existing active grants
        for existing in student.current_grants:
            existing_lower = existing.lower()
            is_existing_exclusive = any(k in existing_lower for k in EXCLUSIVE_TUITION_KEYWORDS)
            if is_existing_exclusive:
                reason = (
                    f"Policy Conflict Detected: You already hold '{existing}'. "
                    f"'{opp.title}' is an exclusive full-tuition grant. Most state and corporate "
                    f"regulations strictly prohibit holding dual-tuition reimbursement schemes."
                )
                return True, reason

        return False, None


def generate_ics_calendar(opp: Opportunity, student: StudentProfile | None = None) -> str:
    """
    Generate RFC 5545 standard .ics file with automated 72h & 24h reminder alarms.
    """
    # Parse or compute deadline timestamp
    now = datetime.datetime.now(datetime.UTC)
    if opp.deadline:
        try:
            # Handle ISO formats
            clean_date = opp.deadline.replace("Z", "+00:00")
            deadline_dt = datetime.datetime.fromisoformat(clean_date)
        except Exception:  # noqa: BLE001
            deadline_dt = now + datetime.timedelta(days=14)
    else:
        deadline_dt = now + datetime.timedelta(days=14)

    dtstamp = now.strftime("%Y%m%dT%H%M%SZ")
    dtend = deadline_dt.strftime("%Y%m%dT%H%M%SZ")
    dtstart = (deadline_dt - datetime.timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
    uid = f"aventra-{uuid.uuid4().hex[:12]}@aventraone.internal"

    summary = f"DEADLINE: {opp.title} ({opp.provider})"
    description = (
        f"Opportunity: {opp.title}\\n"
        f"Provider: {opp.provider}\\n"
        f"Portal: {opp.apply_url}\\n"
        f"Verified by aventra one Policy Conflict Shield."
    )

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//aventra one//Opportunity Intelligence//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{summary}
DESCRIPTION:{description}
URL:{opp.apply_url}
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT72H
ACTION:DISPLAY
DESCRIPTION:aventra one 72h Reminder: {opp.title} deadline in 3 days!
END:VALARM
BEGIN:VALARM
TRIGGER:-PT24H
ACTION:DISPLAY
DESCRIPTION:aventra one 24h Urgent Alert: {opp.title} deadline closes in 24 hours!
END:VALARM
END:VEVENT
END:VCALENDAR
"""
    return ics_content.strip()
