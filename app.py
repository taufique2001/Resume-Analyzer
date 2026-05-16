# IMPORTS

import os
import pdfplumber
from reportlab.pdfgen import canvas

from flask import Flask, render_template, request, send_file

from skills import skills_list

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# FLASK APP SETUP

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# STEP 7 — EXTRACT TEXT FROM PDF

def extract_text_from_pdf(pdf_path):

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            extracted = page.extract_text()

            if extracted:
                text += extracted

    return text.lower()


# STEP 8 — SKILL EXTRACTION

def extract_skills(text):

    found_skills = []

    for skill in skills_list:

        if skill.lower() in text.lower():

            found_skills.append(skill)

    return found_skills


# STEP 9 — ATS SCORE CALCULATION

def calculate_similarity(resume_text, job_description):

    documents = [resume_text, job_description]

    cv = CountVectorizer()

    matrix = cv.fit_transform(documents)

    similarity = cosine_similarity(matrix)[0][1]

    return round(similarity * 100, 2)

# PDF REPORT GENERATION

def create_pdf(score, skills, missing_skills, suggestion):

    pdf_path = "report.pdf"

    c = canvas.Canvas(pdf_path)

    # TITLE

    c.setFont("Helvetica-Bold", 20)

    c.drawString(
        150,
        800,
        "AI Resume Analysis Report"
    )

    # ATS SCORE

    c.setFont("Helvetica", 14)

    c.drawString(
        100,
        750,
        f"ATS Match Score: {score}%"
    )

    # SKILLS FOUND

    c.drawString(
        100,
        710,
        "Skills Found:"
    )

    y = 690

    for skill in skills:

        c.drawString(
            120,
            y,
            f"- {skill}"
        )

        y -= 20

    # MISSING SKILLS

    y -= 20

    c.drawString(
        100,
        y,
        "Missing Skills:"
    )

    y -= 20

    for skill in missing_skills:

        c.drawString(
            120,
            y,
            f"- {skill}"
        )

        y -= 20

    # SUGGESTION

    y -= 30

    c.drawString(
        100,
        y,
        f"AI Recommendation: {suggestion}"
    )

    c.save()

    return pdf_path
# HOME PAGE

@app.route("/")
def home():


    return render_template("index.html")


# ANALYZE ROUTE

@app.route("/analyze", methods=["POST"])

def analyze():

    # GET FILE + JOB DESCRIPTION

    file = request.files["resume"]

    job_description = request.form["job_description"]


    # SAVE RESUME

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)


    # EXTRACT RESUME TEXT

    resume_text = extract_text_from_pdf(filepath)


    # EXTRACT SKILLS

    skills = extract_skills(resume_text)

    job_skills = extract_skills(job_description)


    # ATS SCORE

    score = calculate_similarity(
        resume_text,
        job_description
    )


    # FIND MISSING SKILLS

    missing_skills = []

    for skill in job_skills:

        if skill not in skills:

            missing_skills.append(skill)


    # AI SUGGESTIONS

    if score >= 80:

        suggestion = (
            "Excellent match for this role."
        )

    elif score >= 60:

        suggestion = (
            "Good match. Add more relevant skills to improve ATS score."
        )

    else:

        suggestion = (
            "Resume needs improvement for this role."
        )

    pdf_report = create_pdf(
    score,
    skills,
    missing_skills,
    suggestion
)
    # SEND DATA TO RESULT PAGE

    return render_template(

        "result.html",

        skills=skills,

        score=score,

        missing_skills=missing_skills,

        suggestion=suggestion
    )

@app.route("/download-report")
def download_report():

    return send_file(
        "report.pdf",
        as_attachment=True
    )
# RUN APP

if __name__ == "__main__":

    app.run(debug=True)