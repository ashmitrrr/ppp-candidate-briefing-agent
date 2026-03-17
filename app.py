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

    [data-testid="stSidebar"] { background: #1c1c1e !important; border-right: none; }
    [data-testid="stSidebar"] * { color: #e8e4dd !important; }
    [data-testid="stSidebar"] .stTextInput input {
        background: #2a2a2c !important; border: 1px solid #3a3a3c !important;
        color: #e8e4dd !important; border-radius: 6px;
        font-family: 'DM Mono', monospace; font-size: 0.78rem;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: #2a2a2c !important; border: 1px solid #3a3a3c !important;
        color: #e8e4dd !important; border-radius: 6px;
    }
    [data-testid="stSidebar"] hr { border-color: #3a3a3c !important; }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li { font-size: 0.82rem; color: #888 !important; line-height: 1.6; }
    [data-testid="stSidebar"] h3 {
        font-family: 'Fraunces', serif !important; font-size: 1.1rem !important;
        color: #f0ece4 !important; font-weight: 400 !important; margin-bottom: 1.2rem;
    }

    .ppp-header {
        background: #1c1c1e; padding: 3rem 3rem 2.5rem;
        border-radius: 16px; margin-bottom: 2rem;
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
        color: #f0ece4; margin: 0 0 0.6rem 0; letter-spacing: -0.5px; line-height: 1.15;
    }
    .ppp-header p { color: #888; font-size: 0.9rem; margin: 0; max-width: 500px; line-height: 1.6; }

    .candidate-card {
        background: #fff; border-radius: 14px; padding: 1.75rem 2rem;
        margin-bottom: 1rem; border: 1px solid #ede9e1;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.25rem; gap: 1rem; }
    .card-name { font-family: 'Fraunces', serif; font-size: 1.4rem; font-weight: 400; color: #1c1c1e; margin: 0 0 0.2rem 0; }
    .card-role { font-size: 0.82rem; color: #888; font-family: 'DM Mono', monospace; }
    .scores-row { display: flex; gap: 0.75rem; }
    .score-pill {
        background: #f5f3ef; border: 1px solid #ede9e1; border-radius: 8px;
        padding: 0.5rem 0.9rem; text-align: center; min-width: 72px;
    }
    .score-val { font-family: 'Fraunces', serif; font-size: 1.5rem; font-weight: 400; color: #1c1c1e; line-height: 1; }
    .score-denom { font-size: 0.7rem; color: #aaa; font-family: 'DM Mono', monospace; }
    .score-label { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 1px; color: #aaa; margin-top: 0.3rem; }
    .field-label {
        font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 1.5px; color: #b49b6e; margin: 1.25rem 0 0.4rem 0;
    }
    .field-text { font-size: 0.875rem; color: #3a3a3c; line-height: 1.65; }
    .tag-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.3rem; }
    .tag {
        background: #f5f3ef; border: 1px solid #ede9e1; color: #555;
        font-size: 0.72rem; padding: 0.2rem 0.65rem; border-radius: 4px;
        font-family: 'DM Mono', monospace;
    }
    .outreach-block {
        background: #faf9f6; border-left: 3px solid #b49b6e;
        padding: 0.85rem 1.1rem; border-radius: 0 8px 8px 0; margin-top: 0.4rem;
        font-size: 0.875rem; color: #3a3a3c; font-style: italic; line-height: 1.6;
    }

    .stButton > button[kind="primary"] {
        background: #1c1c1e !important; color: #f0ece4 !important;
        border: none !important; border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
        font-size: 0.9rem !important; padding: 0.65rem 2rem !important;
    }
    .stButton > button[kind="primary"]:hover { background: #2c2c2e !important; }
    .stDownloadButton > button {
        background: transparent !important; border: 1.5px solid #1c1c1e !important;
        color: #1c1c1e !important; border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    }

    [data-testid="stFileUploader"] {
        background: #fff; border: 1.5px dashed #d8d4cc;
        border-radius: 12px; padding: 0.5rem;
    }
    [data-testid="stFileUploader"]:hover { border-color: #b49b6e; }

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
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:86px;margin-bottom:1rem;opacity:0.9;" />'
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
            help="Your key is not stored. It only exists for this session and resets when you close the tab.",
        )

        # set for this session only — never persisted anywhere
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        model = st.selectbox(
            "Model",
            ["claude-sonnet-4-5", "claude-opus-4-5"],
            index=0,
            help="Sonnet is faster and cheaper. Opus for higher quality.",
        )

        st.markdown("---")
        st.markdown("""
**How to use**

1. Enter your Anthropic API key above
2. Upload a candidates CSV
3. Click Generate Briefings
4. Download output.json

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

    st.markdown(f"""
    <div class="candidate-card">
        <div class="card-header">
            <div>
                <div class="card-name">{name}</div>
                <div class="card-role">{role.get('title', '—')} · {role.get('employer', '—')}</div>
            </div>
            <div class="scores-row">
                <div class="score-pill">
                    <div class="score-val">{fit_score}<span class="score-denom">/10</span></div>
                    <div class="score-label">Role Fit</div>
                </div>
                <div class="score-pill">
                    <div class="score-val">{mob_score}<span class="score-denom">/5</span></div>
                    <div class="score-label">Mobility</div>
                </div>
                <div class="score-pill">
                    <div class="score-val">{tenure}<span class="score-denom"> yr</span></div>
                    <div class="score-label">Tenure</div>
                </div>
            </div>
        </div>

        <div class="field-label">Career Narrative</div>
        <div class="field-text">{candidate.get('career_narrative', '—')}</div>

        <div class="field-label">Experience</div>
        <div class="tag-row">{"".join(f'<span class="tag">{t}</span>' for t in tags)}</div>

        <div class="field-label">Firm Context</div>
        <div class="field-text">{candidate.get('firm_aum_context', '—')}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Mobility Rationale</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="field-text">{mob.get("rationale", "—")}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="field-label">Role Fit Justification</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="field-text">{fit.get("justification", "—")}</div>', unsafe_allow_html=True)

    st.markdown('<div class="field-label">Outreach Hook</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="outreach-block">{candidate.get("outreach_hook", "—")}</div>',
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)


def main():
    render_header()
    model = render_sidebar()

    uploaded = st.file_uploader("Upload candidates CSV", type=["csv"], label_visibility="collapsed")

    if uploaded is not None:
        import csv, io
        content = uploaded.getvalue().decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(content)))

        st.markdown(
            f"<p style='font-size:0.82rem;color:#888;margin-bottom:0.75rem;'>{len(rows)} candidates loaded</p>",
            unsafe_allow_html=True
        )
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

                st.markdown("<br>", unsafe_allow_html=True)
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
        st.markdown("""
        <div style='text-align:center;padding:4rem 2rem;'>
            <div style='font-family:Fraunces,serif;font-size:1.1rem;font-weight:300;margin-bottom:0.5rem;color:#888;'>
                Upload a CSV to get started
            </div>
            <div style='font-size:0.82rem;color:#aaa;'>made by Ashmit</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()