def validate_candidate(data: dict) -> tuple[bool, list[str]]:
    errors = []

    required = [
        "candidate_id", "full_name", "current_role", "career_narrative",
        "experience_tags", "firm_aum_context", "mobility_signal",
        "role_fit", "outreach_hook"
    ]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    cr = data.get("current_role", {})
    if not isinstance(cr, dict):
        errors.append("current_role must be an object")
    else:
        for f in ["title", "employer"]:
            if f not in cr or not isinstance(cr[f], str):
                errors.append(f"current_role.{f} must be a string")
        if "tenure_years" not in cr:
            errors.append("current_role.tenure_years is missing")
        elif not isinstance(cr["tenure_years"], (int, float)):
            errors.append("current_role.tenure_years must be a number")

    tags = data.get("experience_tags", [])
    if not isinstance(tags, list) or len(tags) == 0:
        errors.append("experience_tags must be a non-empty list")

    ms = data.get("mobility_signal", {})
    if not isinstance(ms, dict):
        errors.append("mobility_signal must be an object")
    else:
        score = ms.get("score")
        if not isinstance(score, (int, float)) or score < 1 or score > 5:
            errors.append("mobility_signal.score must be 1-5")
        if "rationale" not in ms or not isinstance(ms.get("rationale"), str):
            errors.append("mobility_signal.rationale must be a string")

    rf = data.get("role_fit", {})
    if not isinstance(rf, dict):
        errors.append("role_fit must be an object")
    else:
        if rf.get("role") != "Head of Distribution / National BDM":
            errors.append("role_fit.role value is wrong")
        score = rf.get("score")
        if not isinstance(score, (int, float)) or score < 1 or score > 10:
            errors.append("role_fit.score must be 1-10")
        if "justification" not in rf or not isinstance(rf.get("justification"), str):
            errors.append("role_fit.justification must be a string")

    hook = data.get("outreach_hook", "")
    if not isinstance(hook, str) or len(hook) < 10:
        errors.append("outreach_hook must be a meaningful string")

    return len(errors) == 0, errors


def validate_output(data: dict) -> tuple[bool, list[str]]:
    errors = []

    if "candidates" not in data:
        return False, ["Missing top-level 'candidates' array"]

    candidates = data["candidates"]
    if not isinstance(candidates, list):
        return False, ["'candidates' must be an array"]

    if len(candidates) != 5:
        errors.append(f"Expected 5 candidates, got {len(candidates)}")

    for i, c in enumerate(candidates):
        valid, c_errors = validate_candidate(c)
        if not valid:
            for e in c_errors:
                errors.append(f"Candidate {i+1}: {e}")

    return len(errors) == 0, errors


def strip_confidence_for_output(data: dict) -> tuple[dict, list]:
    # confidence is internal only — strip it from output.json but keep it in the report
    cleaned = {"candidates": []}
    confidence_report = []

    for c in data.get("candidates", []):
        candidate = {k: v for k, v in c.items() if k != "data_confidence"}
        cleaned["candidates"].append(candidate)

        if "data_confidence" in c:
            confidence_report.append({
                "candidate_id": c.get("candidate_id"),
                "full_name": c.get("full_name"),
                "confidence": c["data_confidence"]
            })

    return cleaned, confidence_report