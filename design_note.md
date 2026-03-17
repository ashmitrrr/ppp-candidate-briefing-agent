# Design Note

## Architecture choices and why

The agent runs in two steps: research first, briefing second.

I tried combining web search and JSON generation in a single Claude call. It didn't work reliably — Claude would either cut research short to hit the schema, or produce thorough research that broke the JSON structure. Separating them fixed both problems. The research step can run as many searches as it needs; the briefing step receives clean notes and only has to worry about producing valid JSON.

For web search I used Claude's built-in `web_search_20250305` tool rather than Tavily or SerpAPI. One fewer dependency, one fewer API key for whoever runs this. The research step runs as an agentic loop — Claude decides what to search for, reads results, and decides whether to search again or synthesise. Most candidates need 3–4 searches to build a useful picture.

Rate limiting was the main practical challenge. The free-tier limit of 30k input tokens per minute meant that running research and briefing back-to-back for each candidate hit the cap immediately. The fix was straightforward: 45-second cooldown between research and briefing per candidate, and 90 seconds between candidates. Not elegant, but reliable.

If a candidate can't be found or an API call fails, the agent still produces valid schema-compliant JSON with a low confidence flag rather than crashing. A separate confidence report lets consultants know which briefings need manual verification before acting on them.

## What I'd do differently with more time

The biggest gap is LinkedIn. These candidates almost certainly have detailed profiles, but LinkedIn blocks automated access. With more time I'd look at the LinkedIn API (limited access, requires consent from candidates) or browser automation with Playwright. Neither is simple, but LinkedIn is where the most useful career data lives.

I'd also parallelise with asyncio — all five candidates running concurrently would cut the 10–15 minute runtime to under 3 minutes, once rate limits are handled properly at the concurrent request level.

The prompts would benefit from a feedback loop. What does a PPP consultant actually find useful in a career narrative? What makes a mobility score actionable rather than generic? A few rounds of direct feedback from someone who uses these briefings daily would improve output quality more than any technical change.

The Streamlit UI is functional but basic. A production version would save past runs, let consultants edit briefings inline, export to Word or directly into a CRM, and show candidates side-by-side against the role spec.

## One automation I'd build for PPP if I joined

The first thing I'd build is a market mapping tool.

Every PPP search mandate starts with the same manual process: a consultant takes a role spec and needs to identify 20–50 people who might be worth calling. That means searching LinkedIn, scanning industry news, and relying on the consultant's network knowledge to find who currently holds distribution leadership roles at comparable firms.

I'd automate this. The tool would take a role spec, identify target firms in the relevant AUM range, and surface the people in distribution leadership at each one. The output would be a ranked long list with the same briefing fields as this task, plus a "why now" column — flagging candidates with recent triggers like firm M&A, team restructuring, leadership departures, or fund closures. Those triggers are what turn a cold outreach into a conversation.

The hard part isn't the AI layer. It's building a reliable reference database of Australian fund managers with current AUM, investment style, and distribution team structure. I'd seed it from APRA data for super funds, ASX announcements for listed managers, and industry directories like Financial Standard and Morningstar. Once that reference data exists, the agent's searches become much more targeted and the outputs more accurate — because it's searching with context rather than starting from scratch for each mandate.

This would compress the front end of a search from several days of manual research to a few hours, and let consultants spend that time on what actually drives placements: talking to people.