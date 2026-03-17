# PPP Candidate Briefing Agent

An AI agent that turns a CSV of candidate names into structured recruiter briefings. Built for [Platinum Pacific Partners](https://www.platinumpacificpartners.com.au/).

The agent uses Claude's native web search to research each candidate from public sources, then produces a JSON briefing with career narrative, experience tags, firm AUM context, mobility signal, role fit score, and a personalised outreach hook.

🔗 **Live demo:** 

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd ppp-ai-task
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Add your Anthropic API key to .env

# 3. Run
python run.py candidates.csv
```

Output lands in `output.json`. Takes around 10–15 minutes for 5 candidates due to rate limit cooldowns between steps.

## Usage

### CLI

```bash
python run.py candidates.csv
python run.py candidates.csv --output results.json
python run.py candidates.csv --model claude-opus-4-5
```

### Streamlit UI

```bash
streamlit run app.py
```

Upload a CSV, enter your API key in the sidebar, and click Generate. Briefings render in the browser with a download button for the JSON.

## Architecture

```
candidates.csv
      │
      ▼
┌─────────────┐
│   run.py    │  CLI entry point
└──────┬──────┘
       ▼
┌──────────────────────────────┐
│     agent/pipeline.py        │  loops candidates, calls research → briefing
└──────┬───────────────┬───────┘
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│ researcher  │  │   briefer   │
│             │  │             │
│ Claude +    │  │ Claude →    │
│ web_search  │  │ strict JSON │
│ agentic     │  │             │
│ loop        │  │             │
└─────────────┘  └─────────────┘
       │               │
       ▼               ▼
  research text    structured JSON
                        │
                        ▼
                ┌──────────────┐
                │  schema.py   │  validates output
                └──────┬───────┘
                       ▼
                  output.json
```

**Two-step design:** research and briefing are separate Claude calls. Combining them in one call reliably produced either shallow research or broken JSON — splitting them fixed both. The research step can run as many searches as needed; the briefing step focuses entirely on producing valid JSON from the research notes.

**Agentic web search:** uses Claude's built-in `web_search_20250305` tool. Claude decides what to search and when to stop. No external search API needed.

**Graceful failure:** if research fails or a rate limit can't be recovered, the agent still produces valid schema-compliant JSON with a low confidence flag rather than crashing.

**Rate limiting:** the agent waits 45 seconds between the research and briefing steps for each candidate, and 90 seconds between candidates. This avoids the 30k tokens/minute limit on the free tier. Total runtime is around 10–15 minutes for 5 candidates.

## File Structure

```
ppp-ai-task/
├── run.py                  # CLI
├── app.py                  # Streamlit UI
├── agent/
│   ├── __init__.py
│   ├── pipeline.py         # orchestrator
│   ├── researcher.py       # step 1: web research
│   ├── briefer.py          # step 2: JSON generation
│   ├── prompts.py          # system prompts + role spec
│   └── schema.py           # output validation
├── candidates.csv
├── output.json
├── confidence_report.json
├── requirements.txt
├── design_note.md
├── .env.example
└── .gitignore
```

## Known Limitations

1. **LinkedIn:** LinkedIn blocks programmatic access. The agent uses web search results that reference LinkedIn content — news articles, press releases, announcements — so some career details may be incomplete or inferred.

2. **AUM figures:** sourced from industry publications and may be outdated. Flagged in the confidence report where unverified.

3. **Tenure:** without direct LinkedIn access, start dates are inferred from news coverage. Figures are approximate.

4. **Runtime:** ~10–15 minutes for 5 candidates due to rate limit cooldowns. Parallelising with asyncio would cut this significantly.

5. **Thin profiles:** some candidates have limited public presence outside LinkedIn, which produces lower-confidence briefings.

## What I'd Build Next

See [design_note.md](design_note.md).