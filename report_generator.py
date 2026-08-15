import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def generate_pdf_report(output_path: str, analysis: dict):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    c.setFont('Helvetica-Bold', 16)
    c.drawString(1 * inch, height - 1 * inch, 'AI Resume Analyzer - Report')

    y = height - 1.5 * inch
    c.setFont('Helvetica', 10)

    def write_line(line):
        nonlocal y
        if y < 1 * inch:
            c.showPage()
            y = height - 1 * inch
            c.setFont('Helvetica', 10)
        c.drawString(1 * inch, y, line)
        y -= 12

    write_line(f"Filename: {analysis.get('filename','-')}")
    write_line('')

    write_line('Top Recommendations:')
    for i, rec in enumerate(analysis.get('recommendations', [])[:5], start=1):
        write_line(f"{i}. {rec['role']}: {rec['final_score']}% (TF-IDF {rec['tfidf_score']}%, Skill cov. {rec['skill_coverage']}%)")

    write_line('')
    write_line('Detected Skills:')
    for cat, skills in analysis.get('skills_by_category', {}).items():
        write_line(f"- {cat}: {', '.join(skills)}")

    write_line('')
    write_line('Selected Role Skill Gap:')
    for s in analysis.get('missing_skills', []):
        write_line(f"- {s}")

    write_line('')
    write_line('Learning Roadmap:')
    for step in analysis.get('roadmap', []):
        write_line(f"- {step}")

    c.showPage()
    c.save()
    return output_path
