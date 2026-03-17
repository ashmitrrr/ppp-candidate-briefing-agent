import json
import os
import tempfile
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="PPP Candidate Briefing Agent",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;1,9..144,300;1,9..144,400&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
    html, body, .stApp { background: #f5f3ef !important; font-family: 'DM Sans', sans-serif; }
    [data-testid="stSidebar"] { background: #1c1c1e !important; }
    [data-testid="stSidebar"] * { color: #e8e4dd !important; }
    [data-testid="stSidebar"] .stTextInput input {
        background: #2a2a2c !important; border: 1px solid #3a3a3c !important;
        color: #e8e4dd !important; border-radius: 6px; font-family: 'DM Mono', monospace; font-size: 0.78rem;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: #2a2a2c !important; border: 1px solid #3a3a3c !important; border-radius: 6px;
    }
    [data-testid="stSidebar"] hr { border-color: #3a3a3c !important; }
    [data-testid="stSidebar"] .stMarkdown p { font-size: 0.82rem; color: #888 !important; line-height: 1.6; }
    [data-testid="stSidebar"] h3 {
        font-family: 'Fraunces', serif !important; font-size: 1.1rem !important;
        color: #f0ece4 !important; font-weight: 400 !important;
    }
    .ppp-header {
        background: #1c1c1e; padding: 3rem; border-radius: 16px; margin-bottom: 2rem;
        position: relative; overflow: hidden;
    }
    .ppp-header::before {
        content: ''; position: absolute; top: -60px; right: -60px;
        width: 280px; height: 280px;
        background: radial-gradient(circle, rgba(180,155,110,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .ppp-eyebrow {
        font-family: 'DM Mono', monospace; font-size: 0.68rem;
        letter-spacing: 2.5px; text-transform: uppercase; color: #b49b6e; margin-bottom: 0.75rem;
    }
    .ppp-header h1 {
        font-family: 'Fraunces', serif; font-size: 2.6rem; font-weight: 300;
        color: #f0ece4; margin: 0 0 0.6rem 0; line-height: 1.15;
    }
    .ppp-header p { color: #888; font-size: 0.9rem; margin: 0; max-width: 500px; line-height: 1.6; }
    .stButton > button[kind="primary"] {
        background: #1c1c1e !important; color: #f0ece4 !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 500 !important; font-size: 0.9rem !important;
    }
    .stButton > button[kind="primary"]:hover { background: #2c2c2e !important; }
    .stDownloadButton > button {
        background: transparent !important; border: 1.5px solid #1c1c1e !important;
        color: #1c1c1e !important; border-radius: 8px !important; font-weight: 500 !important;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)


def render_header():
    import base64
    try:
        with open("logo.png", "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:55px;margin-bottom:1rem;opacity:0.9;" />'
    except:
        logo_html = '<div class="ppp-eyebrow">Platinum Pacific Partners</div>'

    st.markdown(f"""
    <div class="ppp-header">
        {logo_html}
        <h1>Candidate<br>Briefing Agent</h1>
        <p>Upload a CSV of candidates. Claude researches each one via web search and returns structured briefings ready for consultant review.</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### Configuration")
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Not stored. Resets when you close the tab.",
        )
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        model = st.selectbox(
            "Model",
            ["claude-sonnet-4-5", "claude-opus-4-5"],
            index=0,
        )
        st.markdown("---")
        st.markdown("""
**How to use**
1. Enter your Anthropic API key
2. Upload a candidates CSV
3. Click Generate Briefings
4. Download output.json

**CSV format**
`full_name, current_employer, current_title, linkedin_url`

**Note:** Each run costs ~$1–4 in API credits.
""")
        return model


def render_candidate(candidate: dict):
    name = candidate.get("full_name", "Unknown")
    role = candidate.get("current_role", {})
    fit = candidate.get("role_fit", {})
    mob = candidate.get("mobility_signal", {})
    tags = candidate.get("experience_tags", [])

    fit_score = fit.get("score", "—")
    mob_score = mob.get("score", "—")
    tenure = role.get("tenure_years", "—")

    with st.container():
        st.markdown(f"### {name}")
        st.caption(f"{role.get('title', '—')} · {role.get('employer', '—')}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Role Fit", f"{fit_score} / 10")
        col2.metric("Mobility", f"{mob_score} / 5")
        col3.metric("Tenure", f"{tenure} yrs")

        st.markdown("**Career Narrative**")
        st.write(candidate.get("career_narrative", "—"))

        if tags:
            st.markdown("**Experience Tags**")
            st.write("  ·  ".join(f"`{t}`" for t in tags))

        st.markdown("**Firm Context**")
        st.write(candidate.get("firm_aum_context", "—"))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Mobility Rationale**")
            st.write(mob.get("rationale", "—"))
        with c2:
            st.markdown("**Role Fit Justification**")
            st.write(fit.get("justification", "—"))

        st.markdown("**Outreach Hook**")
        st.info(candidate.get("outreach_hook", "—"))
        st.divider()


def main():
    render_header()
    model = render_sidebar()

    uploaded = st.file_uploader("Upload candidates CSV", type=["csv"], label_visibility="collapsed")

    if uploaded is not None:
        import csv, io
        content = uploaded.getvalue().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(content)))

        st.caption(f"{len(rows)} candidates loaded")
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if not os.environ.get("ANTHROPIC_API_KEY"):
            st.warning("Enter your Anthropic API key in the sidebar to continue.")
            return

        if st.button("Generate Briefings", type="primary", use_container_width=True):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            output_path = tempfile.mktemp(suffix=".json")
            status = st.status("Researching candidates...", expanded=True)

            def log(msg):
                status.write(msg)

            try:
                from agent.pipeline import run_pipeline
                output = run_pipeline(csv_path=tmp_path, output_path=output_path, model=model, log=log)
                status.update(label="Briefings complete", state="complete")

                st.markdown("---")
                for c in output.get("candidates", []):
                    render_candidate(c)

                st.download_button(
                    "Download output.json",
                    data=json.dumps(output, indent=2, ensure_ascii=False),
                    file_name="output.json",
                    mime="application/json",
                    use_container_width=True,
                )
            except Exception as e:
                status.update(label=f"Failed: {e}", state="error")
                st.error(str(e))
            finally:
                Path(tmp_path).unlink(missing_ok=True)
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:#aaa;font-size:0.9rem;'>Upload a CSV to get started</p>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()