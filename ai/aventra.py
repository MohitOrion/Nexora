"""Ask aventra: Context-Aware Conversational RAG Assistant for aventra one.

Answers questions about matched opportunities, explains the 4-factor scoring
breakdown, warns against policy conflicts, and triggers calendar alerts.
"""

from __future__ import annotations

from typing import Any

try:
    from .conflict_shield import PolicyConflictShield, generate_ics_calendar
    from .gemma_client import GemmaClient
    from .matcher import rank_opportunities
    from .prompts import ASK_aventra_SYSTEM_PROMPT, ASK_aventra_USER_PROMPT
    from .schemas import MatchResult, Opportunity, StudentProfile
except ImportError:  # pragma: no cover - supports direct script execution
    from conflict_shield import PolicyConflictShield, generate_ics_calendar
    from gemma_client import GemmaClient
    from matcher import rank_opportunities
    from prompts import ASK_aventra_SYSTEM_PROMPT, ASK_aventra_USER_PROMPT
    from schemas import MatchResult, Opportunity, StudentProfile


class AskaventraAssistant:
    def __init__(self, client: GemmaClient | None = None):
        self.client = client or GemmaClient()

    def generate_response(
        self,
        query: str,
        student: StudentProfile,
        opportunities: list[Opportunity]
    ) -> dict[str, Any]:
        """Generate context-aware response for student query."""
        ranked_matches = rank_opportunities(student, opportunities)

        # Check for policy conflicts on recommended opportunities
        conflict_warnings = []
        for match in ranked_matches[:5]:
            has_conflict, reason = PolicyConflictShield.check_conflict(student, match.opportunity)
            if has_conflict:
                match.breakdown.conflict_detected = True
                match.breakdown.conflict_reason = reason
                conflict_warnings.append(reason)

        # Build context summary of top opportunities
        summary_lines = []
        for m in ranked_matches[:4]:
            opp = m.opportunity
            b = m.breakdown
            status = "CONFLICT DETECTED" if b.conflict_detected else ("ELIGIBLE" if m.is_eligible else "INELIGIBLE")
            summary_lines.append(
                f"- [{status}] {opp.title} ({opp.provider}): "
                f"Total Score {b.total_score}/100 "
                f"(Academic: {b.academic_score}/35, Domicile: {b.domicile_score}/25, "
                f"Skills: {b.skills_score}/25, Gates: {b.gates_score}/15). "
                f"Deadline: {opp.deadline or 'Not specified'}. "
                f"Gates Passed: {b.passed_gates}."
                + (f" Failures: {', '.join(b.gate_failures)}" if b.gate_failures else "")
                + (f" Warning: {b.conflict_reason}" if b.conflict_reason else "")
            )

        opportunities_summary = "\n".join(summary_lines) if summary_lines else "No opportunities found in cache."

        user_prompt = ASK_aventra_USER_PROMPT.format(
            name=student.name,
            college=student.college,
            college_tier=student.college_tier,
            state_domicile=student.state_domicile,
            degree=student.degree,
            year_of_study=student.year_of_study,
            cgpa=student.cgpa,
            family_income=student.family_income,
            skills=", ".join(student.skills),
            current_grants=", ".join(student.current_grants) if student.current_grants else "None",
            opportunities_summary=opportunities_summary,
            user_query=query
        )

        response_text = self.client.generate(user_prompt, system_instruction=ASK_aventra_SYSTEM_PROMPT)

        # If LLM returned generic fallback or was offline, craft a sharp context answer
        if not response_text or response_text.startswith("I am aventra"):
            response_text = self._fallback_answer(query, student, ranked_matches, conflict_warnings)

        # Check if student asked for calendar sync or ics export
        ics_data = None
        if any(w in query.lower() for w in ["calendar", "ics", "sync", "export", "deadline"]):  # noqa: SIM102
            if ranked_matches:
                ics_data = generate_ics_calendar(ranked_matches[0].opportunity, student)

        return {
            "query": query,
            "response": response_text,
            "top_matches": [m.model_dump() for m in ranked_matches[:5]],
            "conflicts": conflict_warnings,
            "ics_calendar": ics_data
        }

    def _fallback_answer(
        self,
        query: str,
        student: StudentProfile,
        matches: list[MatchResult],
        conflicts: list[str]
    ) -> str:
        """Deterministic context-aware answer when LLM is offline."""
        q_lower = query.lower()
        if "conflict" in q_lower or "dual" in q_lower or "airtel" in q_lower:
            if conflicts:
                return (
                    f"⚠️ **Policy Conflict Alert**: {conflicts[0]}\n\n"
                    "However, developer perks (Google Gemini credits, Adobe Creative Cloud, "
                    "GitHub Student Developer Pack) and hackathons are **100% stackable**!"
                )
            return (
                "✅ Good news! No policy conflicts detected. You can freely apply for these opportunities, "
                "and all developer perks remain 100% stackable."
            )

        if "score" in q_lower or "factor" in q_lower or "formula" in q_lower:
            return (
                "aventra one scores every opportunity using our deterministic 4-factor equation:\n"
                "- **Academic Tier (35 pts)**: College tier & CGPA cutoff clearance.\n"
                "- **State Domicile (25 pts)**: Pan-India or state residency match.\n"
                "- **Skill Overlap (25 pts)**: Resume vector alignment & keyword match.\n"
                "- **Eligibility Gates (15 pts)**: Family income cap, eligible course & study year."
            )

        if matches:
            top = matches[0]
            return (
                f"Based on your profile ({student.college}, CGPA {student.cgpa}, {student.state_domicile} domicile), "
                f"your top verified match is **{top.opportunity.title}** with a match score of "
                f"**{top.breakdown.total_score}/100**.\n\n"
                f"- Academic: {top.breakdown.academic_score}/35\n"
                f"- Domicile: {top.breakdown.domicile_score}/25\n"
                f"- Skills: {top.breakdown.skills_score}/25\n"
                f"- Gates: {top.breakdown.gates_score}/15"
            )

        return "I analyzed your profile against verified opportunities. Upload your resume or ask about specific scholarship criteria!"


class AskIrisAssistant(AskaventraAssistant):
    """Backward compatible alias for the IRIS assistant entry point."""

