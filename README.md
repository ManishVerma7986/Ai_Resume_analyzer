# Career Compass — AI Resume Analyzer

Career Compass analyzes a PDF or DOCX resume and turns it into an interactive career-planning dashboard. It is designed for career guidance, not automated recruiting decisions.

## What it includes

- Role recommendations using blended TF-IDF and skill-coverage scoring
- A modern, responsive Streamlit dashboard with interactive charts and adjustable scoring emphasis
- Target-role skill-gap analysis and a checkable learning roadmap
- Optional job-description keyword alignment
- CSV score export and a downloadable PDF report

Installation:

```
pip install -r requirements.txt
```

Run:

```
streamlit run app.py
```

The app stores generated reports in `reports/`. It contains modules for parsing resumes, cleaning text, extracting skills, matching job roles, generating a learning roadmap, and producing a PDF report.
