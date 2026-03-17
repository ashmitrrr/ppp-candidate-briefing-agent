import anthropic
from .prompts import RESEARCH_SYSTEM_PROMPT

MODEL_DEFAULT = "claude-sonnet-4-5"


def research_candidate(
    client: anthropic.Anthropic,
    name: str,
    employer: str,
    title: str,
    model: str = MODEL_DEFAULT,
) -> str:
    user_message = (
        f"Research this candidate for a Head of Distribution / National BDM role:\n\n"
        f"Name: {name}\n"
        f"Current employer: {employer}\n"
        f"Current title: {title}\n"
        f"Industry: Australian funds management\n\n"
        f"Run up to 4 targeted searches. Find their career history, current firm AUM, "
        f"any recent news or moves, and their industry profile. "
        f"Be specific about what you found vs what you're inferring."
    )

    messages = [{"role": "user", "content": user_message}]

    for _ in range(8):
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=RESEARCH_SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            text_parts = [
                block.text for block in response.content
                if hasattr(block, "text")
            ]
            return "\n".join(text_parts)

        # keep going if claude used tools
        has_tool_use = any(
            getattr(block, "type", None) == "tool_use"
            for block in response.content
        )

        if not has_tool_use:
            text_parts = [
                block.text for block in response.content
                if hasattr(block, "text")
            ]
            return "\n".join(text_parts) if text_parts else "No research data found."

        messages.append({
            "role": "user",
            "content": "Synthesize what you've found so far into a research brief now."
        })

    return "Research incomplete — hit iteration limit."