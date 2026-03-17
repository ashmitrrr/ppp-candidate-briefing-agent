import csv
import json
import time
from pathlib import Path
from typing import Callable

import anthropic

from .researcher import research_candidate
from .briefer import generate_briefing
from .schema import validate_output, strip_confidence_for_output

MODEL_DEFAULT = "claude-sonnet-4-5"


def load_candidates(csv_path: str) -> list[dict]:
    candidates = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candidates.append({
                "full_name": row["full_name"].strip(),
                "current_employer": row["current_employer"].strip(),
                "current_title": row["current_title"].strip(),
                "linkedin_url": row.get("linkedin_url", "").strip(),
            })
    return candidates


def run_pipeline(
    csv_path: str,
    output_path: str = "output.json",
    model: str = MODEL_DEFAULT,
    log: Callable[[str], None] = print,
) -> dict:
    client = anthropic.Anthropic()

    log(f"Loading candidates from {csv_path}...")
    candidates = load_candidates(csv_path)
    log(f"Found {len(candidates)} candidates.\n")

    briefings = []

    for i, candidate in enumerate(candidates):
        candidate_id = f"candidate_{i + 1}"
        name = candidate["full_name"]
        employer = candidate["current_employer"]
        title = candidate["current_title"]

        log(f"{'='*60}")
        log(f"[{i+1}/{len(candidates)}] {name}")
        log(f"  {title} at {employer}")
        log(f"{'='*60}")

        # step 1: research
        log(f"  Researching...")
        start = time.time()
        research_data = None
        for attempt in range(3):
            try:
                research_data = research_candidate(client, name, employer, title, model=model)
                log(f"  Research complete ({time.time() - start:.1f}s)")
                log(f"  Preview: {research_data[:200].replace(chr(10), ' ')}...")
                break
            except anthropic.RateLimitError:
                wait = 65 * (attempt + 1)
                log(f"  Rate limited. Waiting {wait}s... ({attempt+1}/3)")
                time.sleep(wait)
            except Exception as e:
                log(f"  Research failed: {e}")
                break

        if research_data is None:
            research_data = f"Research failed for {name}. Known: {title} at {employer}."

        # gap between research and briefing — web search burns a lot of tokens
        log(f"  Cooling down 45s before briefing...")
        time.sleep(45)

        # step 2: briefing
        log(f"  Generating briefing...")
        start = time.time()
        briefing = None
        for attempt in range(3):
            try:
                briefing = generate_briefing(
                    client, candidate_id, name, employer, title, research_data, model=model
                )
                log(f"  Briefing complete ({time.time() - start:.1f}s)")
                log(f"  Role fit: {briefing.get('role_fit', {}).get('score', '?')}/10 | "
                    f"Mobility: {briefing.get('mobility_signal', {}).get('score', '?')}/5 | "
                    f"Confidence: {briefing.get('data_confidence', {}).get('overall', '?')}")
                break
            except anthropic.RateLimitError:
                wait = 65 * (attempt + 1)
                log(f"  Rate limited. Waiting {wait}s... ({attempt+1}/3)")
                time.sleep(wait)
            except Exception as e:
                log(f"  Briefing failed: {e}")
                break

        if briefing is None:
            briefing = {
                "candidate_id": candidate_id,
                "full_name": name,
                "current_role": {"title": title, "employer": employer, "tenure_years": 0.0},
                "career_narrative": f"Briefing generation failed for {name}.",
                "experience_tags": ["distribution"],
                "firm_aum_context": f"Currently at {employer}.",
                "mobility_signal": {"score": 3, "rationale": "Unable to assess."},
                "role_fit": {
                    "role": "Head of Distribution / National BDM",
                    "score": 5,
                    "justification": "Unable to assess due to error.",
                },
                "outreach_hook": f"Your background at {employer} is relevant to a role we are working on.",
                "data_confidence": {"overall": "low", "unverified_fields": ["all"]},
            }

        briefings.append(briefing)
        log("")

        # wait between candidates so we don't hit the per-minute token limit
        if i < len(candidates) - 1:
            log(f"  Waiting 90s before next candidate...")
            time.sleep(90)

    full_output = {"candidates": briefings}
    clean_output, confidence_report = strip_confidence_for_output(full_output)

    log("Validating schema...")
    is_valid, errors = validate_output(clean_output)
    if is_valid:
        log("Schema validation passed.")
    else:
        for e in errors:
            log(f"  - {e}")

    output_file = Path(output_path)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean_output, f, indent=2, ensure_ascii=False)
    log(f"\nOutput written to {output_file}")

    confidence_path = output_file.parent / "confidence_report.json"
    with open(confidence_path, "w", encoding="utf-8") as f:
        json.dump(confidence_report, f, indent=2, ensure_ascii=False)
    log(f"Confidence report written to {confidence_path}")

    return clean_output