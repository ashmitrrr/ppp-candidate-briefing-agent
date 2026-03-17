import json
import anthropic
from .prompts import BRIEFING_SYSTEM_PROMPT

MODEL_DEFAULT = "claude-sonnet-4-5"


def generate_briefing(
    client: anthropic.Anthropic,
    candidate_id: str,
    name: str,
    employer: str,
    title: str,
    research_data: str,
    model: str = MODEL_DEFAULT,
) -> dict:
    user_message = (
        f"Produce a candidate briefing JSON for the following candidate.\n\n"
        f"CANDIDATE INPUT:\n"
        f"- candidate_id: {candidate_id}\n"
        f"- Full name: {name}\n"
        f"- Current employer: {employer}\n"
        f"- Current title: {title}\n\n"
        f"RESEARCH DATA:\n{research_data}\n\n"
        f"Return ONLY valid JSON. No markdown fences, no explanation."
    )

    last_error = None
    for attempt in range(3):
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=BRIEFING_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = "".join(
            block.text for block in response.content
            if hasattr(block, "text")
        ).strip()

        # strip markdown fences if claude adds them anyway
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        try:
            briefing = json.loads(raw_text)

            briefing["candidate_id"] = candidate_id

            if "role_fit" in briefing:
                briefing["role_fit"]["role"] = "Head of Distribution / National BDM"

            if "current_role" in briefing:
                ty = briefing["current_role"].get("tenure_years")
                if isinstance(ty, str):
                    try:
                        briefing["current_role"]["tenure_years"] = float(ty)
                    except ValueError:
                        briefing["current_role"]["tenure_years"] = 0.0

            if "mobility_signal" in briefing:
                briefing["mobility_signal"]["score"] = int(
                    briefing["mobility_signal"].get("score", 3)
                )
            if "role_fit" in briefing:
                briefing["role_fit"]["score"] = int(
                    briefing["role_fit"].get("score", 5)
                )

            return briefing

        except json.JSONDecodeError as e:
            last_error = e
            # tell claude what went wrong so it can fix it
            user_message = (
                f"Your previous response was not valid JSON. Error: {e}\n\n"
                f"Try again. Return ONLY a valid JSON object — no markdown, "
                f"no backticks, no text before or after.\n\n"
                f"CANDIDATE INPUT:\n"
                f"- candidate_id: {candidate_id}\n"
                f"- Full name: {name}\n"
                f"- Current employer: {employer}\n"
                f"- Current title: {title}\n\n"
                f"RESEARCH DATA:\n{research_data}"
            )

    return _fallback_briefing(candidate_id, name, employer, title, str(last_error))


def _fallback_briefing(
    candidate_id: str, name: str, employer: str, title: str, error: str
) -> dict:
    # used when all retries fail — still returns valid schema so output.json never breaks
    return {
        "candidate_id": candidate_id,
        "full_name": name,
        "current_role": {
            "title": title,
            "employer": employer,
            "tenure_years": 0.0,
        },
        "career_narrative": (
            f"{name} is currently {title} at {employer}. "
            f"Automated research was unable to produce a complete briefing. "
            f"Manual review recommended."
        ),
        "experience_tags": ["distribution"],
        "firm_aum_context": f"Currently at {employer}. AUM not verified.",
        "mobility_signal": {
            "score": 3,
            "rationale": "Insufficient data to assess mobility.",
        },
        "role_fit": {
            "role": "Head of Distribution / National BDM",
            "score": 5,
            "justification": (
                "Unable to fully assess fit due to incomplete research data. "
                "Title and employer suggest potential relevance. Manual review needed."
            ),
        },
        "outreach_hook": (
            f"We are working with a mid-tier Australian asset manager building out "
            f"their distribution leadership and your background at {employer} caught our attention."
        ),
        "data_confidence": {
            "overall": "low",
            "unverified_fields": ["all fields — automated research failed"],
        },
    }