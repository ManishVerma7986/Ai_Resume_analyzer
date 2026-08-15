import os
import re
import hashlib
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import DATA_DIR, MAX_UPLOAD_SIZE_MB, REPORTS_DIR
from job_matcher import compute_similarity_scores, load_job_roles
from report_generator import generate_pdf_report
from resume_parser import extract_resume_text
from roadmap_generator import generate_roadmap
from skill_extractor import extract_skills_from_text
from text_cleaner import normalize_text


st.set_page_config(
    page_title="Career Compass | Resume Analyzer",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles():
    st.markdown(
        """
        <style>
        :root { --ink: #11203b; --muted: #64748b; --line: #e6eaf1; --brand: #635bff; --mint: #16bca1; }
        .stApp { background: #f7f8fc; color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(247, 248, 252, .82); backdrop-filter: blur(12px); }
        [data-testid="stSidebar"] { background: #101a35; }
        [data-testid="stSidebar"] * { color: #eef2ff !important; }
        [data-testid="stSidebar"] .stFileUploader, [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background: rgba(255,255,255,.07); border-color: rgba(255,255,255,.18); }
        .block-container { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 3rem; }
        .hero { position: relative; overflow: hidden; padding: 2.4rem; border-radius: 26px; color: white; background: linear-gradient(125deg, #111c3d 0%, #3e38aa 55%, #6b5dff 100%); box-shadow: 0 18px 45px rgba(48, 45, 133, .22); animation: rise .55s ease-out both; }
        .hero:after { content: ''; position: absolute; width: 360px; height: 360px; right: -100px; top: -180px; border-radius: 50%; background: radial-gradient(circle, rgba(68,227,199,.55), rgba(255,255,255,0) 68%); }
        .eyebrow { font-size: .75rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: #93f3df; margin-bottom: .7rem; }
        .hero h1 { position: relative; z-index: 1; font-size: clamp(2rem, 4vw, 3.25rem); line-height: 1.04; margin: 0; letter-spacing: -.04em; }
        .hero p { position: relative; z-index: 1; max-width: 630px; margin: .85rem 0 0; color: #dbe5ff; font-size: 1.05rem; }
        .section-title { margin: 2.1rem 0 .25rem; font-size: 1.28rem; font-weight: 800; letter-spacing: -.02em; }
        .section-kicker { color: var(--muted); margin-bottom: 1rem; }
        .metric-card { height: 100%; min-height: 126px; box-sizing: border-box; padding: 1.1rem 1.2rem; border-radius: 18px; background: #fff; border: 1px solid var(--line); box-shadow: 0 6px 20px rgba(15, 23, 42, .045); animation: rise .5s ease-out both; }
        .metric-label { color: var(--muted); font-size: .8rem; font-weight: 700; text-transform: uppercase; letter-spacing: .065em; }
        .metric-value { margin-top: .45rem; color: var(--ink); font-size: 2rem; line-height: 1; font-weight: 800; letter-spacing: -.045em; }
        .metric-note { color: var(--muted); font-size: .83rem; margin-top: .6rem; }
        .panel { padding: 1.25rem; border-radius: 18px; background: #fff; border: 1px solid var(--line); box-shadow: 0 6px 20px rgba(15, 23, 42, .04); }
        .skill-pill { display: inline-block; margin: .24rem .28rem .1rem 0; padding: .35rem .63rem; border-radius: 999px; background: #eef1ff; color: #4037aa; font-size: .84rem; font-weight: 650; }
        .missing-pill { background: #fff1ed; color: #c04d2c; }
        .empty-state { text-align: center; padding: 2.4rem 1.5rem; background: white; border: 1px dashed #cdd5e1; border-radius: 20px; }
        .empty-orb { display: inline-grid; place-items: center; width: 56px; height: 56px; border-radius: 16px; background: #ecebff; color: #5449e8; font-size: 1.6rem; }
        .stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 700; border: 0; padding: .58rem 1rem; transition: transform .18s ease, box-shadow .18s ease; }
        .stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(80, 70, 220, .18); }
        [data-testid="stFileUploaderDropzone"] { border-radius: 14px; }
        div[data-testid="stMetric"] { background: white; border: 1px solid var(--line); padding: .8rem; border-radius: 14px; }
        @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def pills(items, missing=False):
    if not items:
        return "<span style='color:#64748b'>None detected yet</span>"
    kind = " missing-pill" if missing else ""
    return "".join(f"<span class='skill-pill{kind}'>{item}</span>" for item in items)


def insight_from_score(score):
    if score >= 70:
        return "Strong alignment. Focus on explaining your impact in interviews."
    if score >= 45:
        return "Promising fit. Close a few targeted skill gaps to improve your profile."
    return "Early-stage fit. Use the roadmap to build evidence for this direction."


def extract_keywords(text, limit=12):
    words = re.findall(r"\b[a-zA-Z][a-zA-Z+#.]{2,}\b", text.lower())
    stop_words = {"and", "the", "with", "for", "that", "this", "from", "you", "your", "are", "our", "will", "have", "has", "job", "role", "work", "team", "years", "experience", "skills", "using", "their", "into", "they"}
    return [word for word, _ in Counter(word for word in words if word not in stop_words).most_common(limit)]


@st.cache_data(show_spinner=False)
def load_roles(path):
    return load_job_roles(path)


def build_report(analysis):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", analysis["filename"])
    report_path = os.path.join(REPORTS_DIR, f"career_compass_{safe_name}.pdf")
    generate_pdf_report(report_path, analysis)
    with open(report_path, "rb") as report_file:
        return report_file.read(), os.path.basename(report_path)


inject_styles()

with st.sidebar:
    st.markdown("## ✦ Career Compass")
    st.caption("Resume intelligence, made practical.")
    st.divider()
    uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"], help=f"PDF or DOCX, up to {MAX_UPLOAD_SIZE_MB} MB")
    st.caption("Your file is used only for the analysis in this session.")
    st.divider()
    st.markdown("**How it works**")
    st.caption("1. Extract skills\n\n2. Compare career paths\n\n3. Build an action plan")

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Career intelligence dashboard</div>
      <h1>Turn your resume into<br/>your next best move.</h1>
      <p>Discover matching roles, uncover the skills that matter most, and leave with a focused learning plan.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if uploaded_file is None:
    st.markdown("<div class='section-title'>Start with your resume</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>Upload a PDF or DOCX from the sidebar to unlock your personalized dashboard.</div>", unsafe_allow_html=True)
    feature_cols = st.columns(3)
    feature_data = [
        ("01", "Role matching", "See the career paths your experience aligns with."),
        ("02", "Skill gaps", "Find the highest-value skills to add next."),
        ("03", "Action plan", "Track a practical, role-specific learning roadmap."),
    ]
    for column, (number, title, description) in zip(feature_cols, feature_data):
        with column:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>{number}</div><div style='font-size:1.15rem;font-weight:800;margin-top:.55rem'>{title}</div><div class='metric-note'>{description}</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='empty-state' style='margin-top:1.5rem'><div class='empty-orb'>↑</div><h3 style='margin:.7rem 0 .25rem'>Ready when you are</h3><span style='color:#64748b'>Your analysis appears here after you choose a file.</span></div>", unsafe_allow_html=True)
    st.stop()

uploaded_file.seek(0, os.SEEK_END)
size_mb = uploaded_file.tell() / (1024 * 1024)
uploaded_file.seek(0)
if size_mb > MAX_UPLOAD_SIZE_MB:
    st.error(f"This file is {size_mb:.1f} MB. Please upload a resume smaller than {MAX_UPLOAD_SIZE_MB} MB.")
    st.stop()

uploaded_file.seek(0)
file_key = hashlib.sha256(uploaded_file.read()).hexdigest()
uploaded_file.seek(0)
if st.session_state.get("file_key") != file_key:
    with st.spinner("Reading your resume and mapping its skills..."):
        resume_text, error = extract_resume_text(uploaded_file)
    if error:
        st.error(error)
        st.stop()
    st.session_state.file_key = file_key
    st.session_state.cleaned_resume = normalize_text(resume_text)
    st.session_state.completed_steps = set()
    st.session_state.pdf_key = None

cleaned_resume = st.session_state.cleaned_resume
if not cleaned_resume.strip():
    st.error("We could not find readable text in this document. Please try a text-based PDF or DOCX.")
    st.stop()

skills_by_category, detected_skills = extract_skills_from_text(cleaned_resume, os.path.join(DATA_DIR, "skill_dictionary.csv"))
job_roles = load_roles(os.path.join(DATA_DIR, "job_roles.csv"))

with st.expander("Tune the matching model", expanded=False):
    left, right = st.columns(2)
    with left:
        skill_weight = st.slider("Importance of skills", 0.1, 0.8, 0.45, 0.05, help="Increase this if your skills list should matter more than phrasing in the resume.")
    with right:
        st.caption("The remaining weight is based on resume-to-role language similarity.")

results = compute_similarity_scores(
    cleaned_resume,
    job_roles,
    tfidf_weight=round(1 - skill_weight, 2),
    skill_weight=skill_weight,
    detected_skills=detected_skills,
)
df = pd.DataFrame(results)
top_match = results[0]

st.markdown("<div class='section-title'>Your career snapshot</div>", unsafe_allow_html=True)
snapshot = st.columns(4)
cards = [
    ("Best fit", top_match["role"], f"{top_match['final_score']}% match score"),
    ("Skills found", str(len(detected_skills)), f"Across {len(skills_by_category)} categories"),
    ("Resume signals", str(len(cleaned_resume.split())), "Words successfully extracted"),
    ("Paths explored", str(len(results)), "Career directions compared"),
]
for column, (label, value, note) in zip(snapshot, cards):
    with column:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)

left_col, right_col = st.columns([1.28, .72], gap="large")
with left_col:
    st.markdown("<div class='section-title'>Role compatibility</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>A blended score from relevant resume language and required-skill coverage.</div>", unsafe_allow_html=True)
    chart_df = df.sort_values("final_score")
    fig = px.bar(chart_df, x="final_score", y="role", orientation="h", text="final_score", color="final_score", color_continuous_scale=["#c9c6ff", "#635bff", "#17b89d"])
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False, hovertemplate="<b>%{y}</b><br>Match score: %{x:.1f}%<extra></extra>")
    fig.update_layout(height=350, margin=dict(l=0, r=45, t=8, b=0), coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(title="", range=[0, 105], showgrid=True, gridcolor="#edf0f5"), yaxis=dict(title=""), font=dict(color="#24324b"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
with right_col:
    st.markdown("<div class='section-title'>Top direction</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='panel'><div class='eyebrow' style='color:#635bff'>{top_match['final_score']}% compatibility</div><div style='font-size:1.5rem;font-weight:800;letter-spacing:-.03em'>{top_match['role']}</div><p style='color:#64748b;font-size:.92rem;margin:.6rem 0 1rem'>{insight_from_score(top_match['final_score'])}</p><div style='color:#64748b;font-size:.78rem;text-transform:uppercase;font-weight:800;letter-spacing:.06em'>Skill coverage</div><div style='font-size:1.45rem;font-weight:800;margin-top:.2rem'>{top_match['skill_coverage']}%</div></div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Explore your target role</div>", unsafe_allow_html=True)
target = st.selectbox("Choose a role to inspect", df["role"].tolist(), label_visibility="collapsed")
selected = next(result for result in results if result["role"] == target)
required_skills = selected["required_skills"]
detected_lower = {skill.lower() for skill in detected_skills}
found = [skill for skill in required_skills if skill.lower() in detected_lower]
missing = [skill for skill in required_skills if skill.lower() not in detected_lower]
coverage_pct = round((len(found) / len(required_skills) * 100), 1) if required_skills else 0

details_left, details_right = st.columns([.9, 1.1], gap="large")
with details_left:
    radar = go.Figure(go.Indicator(
        mode="gauge+number",
        value=coverage_pct,
        number={"suffix": "%", "font": {"size": 42, "color": "#11203b"}},
        title={"text": "Target-role skill coverage", "font": {"size": 16, "color": "#64748b"}},
        gauge={"axis": {"range": [0, 100], "visible": False}, "bar": {"color": "#635bff", "thickness": .72}, "bgcolor": "#edf0fb", "borderwidth": 0, "steps": [{"range": [0, 100], "color": "#edf0fb"}]},
    ))
    radar.update_layout(height=230, margin=dict(l=20, r=20, t=55, b=8), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(radar, use_container_width=True, config={"displayModeBar": False})
with details_right:
    st.markdown("<div class='panel'><div style='font-weight:800;margin-bottom:.35rem'>Skills already in your resume</div>" + pills(found) + "<div style='font-weight:800;margin:1rem 0 .35rem'>High-value skills to build next</div>" + pills(missing, missing=True) + "</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Tailor for a specific opportunity</div>", unsafe_allow_html=True)
job_description = st.text_area("Paste a job description (optional)", placeholder="Paste a job post here to see overlapping keywords and phrases...", height=120)
if job_description.strip():
    job_keywords = extract_keywords(job_description)
    resume_lower = cleaned_resume.lower()
    overlap = [keyword for keyword in job_keywords if re.search(rf"\b{re.escape(keyword)}\b", resume_lower)]
    alignment = round((len(overlap) / len(job_keywords) * 100), 1) if job_keywords else 0
    one, two = st.columns([.3, .7])
    with one:
        st.metric("Keyword alignment", f"{alignment}%", help="Share of prominent job-description keywords that appear in the extracted resume text.")
    with two:
        st.markdown("<div class='panel'><div style='font-weight:800;margin-bottom:.35rem'>Overlapping job keywords</div>" + pills(overlap) + "<div style='font-weight:800;margin:1rem 0 .35rem'>Consider adding evidence for</div>" + pills([word for word in job_keywords if word not in overlap], missing=True) + "</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Your focused learning plan</div>", unsafe_allow_html=True)
roadmap = generate_roadmap(missing)
if not missing:
    st.success("You cover every listed skill for this role. Strengthen your portfolio and quantify the impact of your projects.")
for index, step in enumerate(roadmap):
    step_key = f"{file_key}:{target}:{index}"
    completed = st.checkbox(step, value=step_key in st.session_state.completed_steps, key=f"roadmap_{step_key}")
    if completed:
        st.session_state.completed_steps.add(step_key)
    else:
        st.session_state.completed_steps.discard(step_key)

st.markdown("<div class='section-title'>Export and compare</div>", unsafe_allow_html=True)
export_left, export_right, export_note = st.columns([.38, .38, .24], vertical_alignment="center")
with export_left:
    st.download_button("Download scores as CSV", df[["role", "final_score", "skill_coverage", "tfidf_score"]].to_csv(index=False).encode("utf-8"), file_name="career-match-scores.csv", mime="text/csv", use_container_width=True)

analysis = {
    "filename": uploaded_file.name,
    "recommendations": results,
    "skills_by_category": skills_by_category,
    "missing_skills": missing,
    "roadmap": roadmap,
    "target_role": target,
}
analysis_key = f"{file_key}:{target}:{skill_weight}"
if st.session_state.get("pdf_key") != analysis_key:
    with st.spinner("Preparing your polished report..."):
        st.session_state.pdf_data, st.session_state.pdf_name = build_report(analysis)
        st.session_state.pdf_key = analysis_key
with export_right:
    st.download_button("Download PDF report", st.session_state.pdf_data, file_name=st.session_state.pdf_name, mime="application/pdf", use_container_width=True)
with export_note:
    st.caption("Scores are career-guidance estimates, not recruiter decisions.")
