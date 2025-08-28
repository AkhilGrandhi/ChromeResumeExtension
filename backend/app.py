from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from openai import OpenAI
from io import BytesIO
import re
import traceback

# ------- Word (python-docx) -------
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# ------- PDF (reportlab) -------
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
from reportlab.lib.units import inch

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

#Skills Section Titles
SECTION_TITLES = {
    "professional summary",
    "summary",
    "technical skills",
    "skills",
    "professional experience",
    "experience",
    "work experience",
    "work history",
    "education",
    "certifications",
    "projects",
    "additional qualifications",
    "additional information",
    "references",
}

def clean_markdown(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = text.replace("`", "")
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("*", "").replace("_", "")
    text = re.sub(r"^\s*[•\-–]\s*", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def is_contact_line(line: str) -> bool:
    if not line:
        return False
    l = line.lower()
    return ("email" in l or "@" in l or "phone" in l or re.search(r"\b\d{10}\b", l) or re.search(r"\+\d", l))

def is_section_title(line: str) -> bool:
    if not line:
        return False
    raw = line.strip().rstrip(":")
    return raw.lower() in SECTION_TITLES

def add_horizontal_rule(paragraph):
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    pPr.append(pBdr)

def create_resume_word(content: str) -> Document:
    doc = Document()

    # Margins
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    # Default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    lines = [str(ln).strip("• ").strip() for ln in content.splitlines() if ln and str(ln).strip()]
    idx = 0
    print("Lines",lines)
    # Candidate Name
    if idx < len(lines):
        name_para = doc.add_paragraph(lines[idx])
        name_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = name_para.runs[0]
        run.bold = True
        run.font.size = Pt(20)
        idx += 1

        # Email + Phone + Location (always formatted as "Email: ... | Mobile: ... | Location: ...")
    contact_email, contact_phone, contact_location = "", "", ""
    while idx < len(lines) and is_contact_line(lines[idx]):
        line = lines[idx]

        # Extract email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", line)
        if email_match:
            contact_email = email_match.group(0)

        # Extract phone (10+ digits)
        phone_match = re.search(r"(\+?\d[\d\s\-]{8,}\d)", line)
        if phone_match:
            contact_phone = phone_match.group(0).strip()

        # Extract location (after "Location:" or last segment if present)
        loc_match = re.search(r"Location\s*[:\-]?\s*(.*)", line, re.IGNORECASE)
        if loc_match:
            contact_location = loc_match.group(1).strip()

        idx += 1

    if contact_email or contact_phone or contact_location:
        pieces = []
        if contact_email:
            pieces.append(f"Email: {contact_email}")
        if contact_phone:
            pieces.append(f"Mobile: {contact_phone}")
        if contact_location:
            pieces.append(f"Location: {contact_location}")
        contact_line = "  |  ".join(pieces)

        contact_para = doc.add_paragraph(contact_line)
        contact_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        contact_para.runs[0].font.size = Pt(11)



    # # Body parsing
    # skill_categories = [
    #     "Programming Languages", "Cloud Platforms", "Big Data Ecosystems",
    #     "Azure Services", "Database Management", "BI & Reporting Tools",
    #     "ETL & Data Integration", "Orchestration & Automation",
    #     "Version Control", "Operating Systems"
    # ]

    skill_categories =  [
    # Programming & Development
    "Programming Languages",
    "Back-End Development Frameworks",
    "Front-End Technologies",
    "JavaScript Frameworks & Libraries",
    "Mobile App Development Frameworks",
    "Cross-Platform Development",
    "API Development & Integration",
    "Web Development",
    "Game Development Tools",

    # Cloud Computing & Platforms
    "Cloud Platforms",
    "Azure Services",
    "AWS Services",
    "Google Cloud Services",
    "Hybrid & Multi-Cloud Architectures",

    # DevOps, CI/CD & Automation
    "CI/CD Tools",
    "DevOps Tools & Practices",
    "Infrastructure as Code",
    "Configuration Management Tools",
    "Containerization & Orchestration",
    "Monitoring & Observability Tools",
    "Scripting & Automation",

    # Data & Analytics
    "Big Data Ecosystems",
    "ETL & Data Integration Tools",
    "Data Warehousing Solutions",
    "Database Management Systems",
    "Data Lake & Lakehouse Technologies",
    "Data Modeling & Architecture",
    "Data Governance & Lineage",

    # AI, ML & Data Science
    "Machine Learning Frameworks",
    "Natural Language Processing",
    "Computer Vision",
    "Model Training & Deployment",
    "AI/ML Ops Tools",
    "Data Science Tools",
    "Statistical Analysis & Modeling",

    # Cybersecurity & Compliance
    "Security & Compliance Tools",
    "Cloud Security",
    "Network Security",
    "Application Security",
    "Identity & Access Management",
    "Security Information and Event Management",
    "Penetration Testing & Ethical Hacking",

    # Testing & Quality Assurance
    "Automated Testing Tools",
    "Performance Testing Tools",
    "Test Management Tools",
    "API Testing Tools",
    "Unit & Integration Testing Frameworks",
    "QA Processes & Methodologies",

    # UI/UX & Design
    "UI/UX Design Tools",
    "Wireframing & Prototyping Tools",
    "Design Systems & Pattern Libraries",
    "User Research & Usability Testing",

    # Digital Productivity & IDEs
    "Version Control Systems",
    "Integrated Development Environments",
    "Code Collaboration Tools",
    "Task & Issue Tracking Tools",
    "Documentation Tools",

    # Operating Systems & Platforms
    "Operating Systems",
    "Virtualization Tools",
    "Desktop & Server Administration",

    # Emerging & Specialized Technologies
    "Blockchain Development",
    "IoT Development & Platforms",
    "Edge Computing",
    "Augmented Reality / Virtual Reality",
    "Quantum Computing Fundamentals"
    ]



    while idx < len(lines):
        line = lines[idx]

        # Section Titles
        if is_section_title(line):
            p = doc.add_paragraph(line.upper().rstrip(":"))
            r = p.runs[0]
            r.bold = True
            r.font.size = Pt(11)
            add_horizontal_rule(p)
            idx += 1
            continue

        # Skill Categories
        if any(line.startswith(cat) for cat in skill_categories):
            category = line.strip()
            skills = []
            idx += 1
            while idx < len(lines) and not is_section_title(lines[idx]) and not any(lines[idx].startswith(cat) for cat in skill_categories):
                skills.append(lines[idx].lstrip("-• ").strip())
                idx += 1

            p = doc.add_paragraph()
            r1 = p.add_run(category + ": ")
            r1.bold = True
            r1.font.size = Pt(11)
            r2 = p.add_run(", ".join(skills))
            r2.font.size = Pt(11)
            continue

        # Technologies Used (only heading bold)
        if line.startswith("Technologies Used"):
            if ":" in line:
                heading, techs = line.split(":", 1)
                p = doc.add_paragraph()
                r1 = p.add_run(heading.strip() + ": ")
                r1.bold = True
                r1.font.size = Pt(11)
                r2 = p.add_run(techs.strip())  # not bold
                r2.font.size = Pt(11)
            else:
                p = doc.add_paragraph()
                r1 = p.add_run(line.strip())
                r1.bold = True
                r1.font.size = Pt(11)
            idx += 1
            continue

        # Bullets
        if line.startswith("- "):
            bullet_para = doc.add_paragraph(line[2:].strip(), style="List Bullet")
            bullet_para.paragraph_format.left_indent = Inches(0.25)
            idx += 1
            continue

        # Fallback: normal text
        para = doc.add_paragraph(line)
        idx += 1

    return doc


def create_resume_pdf(content: str) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.5*inch, rightMargin=0.5*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("TitleCenter", parent=styles["Heading1"], alignment=1, fontSize=18, leading=22, spaceAfter=6)
    contact_style = ParagraphStyle("Contact", parent=styles["Normal"], alignment=1, fontSize=10, leading=14, spaceAfter=2)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=6, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=11, leading=15, spaceAfter=4)
    bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=11, leading=15, leftIndent=20, bulletIndent=10, spaceAfter=2)

    story = []
    lines = [ln.strip() for ln in content.splitlines() if ln is not None]

    i = 0
    while i < len(lines) and not lines[i]:
        i += 1
    if i < len(lines):
        story.append(Paragraph(lines[i], title_style))
        i += 1

    contact_added = 0
    while i < len(lines) and contact_added < 4 and is_contact_line(lines[i]):
        if lines[i]:
            story.append(Paragraph(lines[i], contact_style))
            contact_added += 1
        i += 1
    story.append(Spacer(1, 6))

    while i < len(lines):
        line = lines[i]
        if not line:
            story.append(Spacer(1, 4))
            i += 1
            continue
        if is_section_title(line):
            story.append(Paragraph(line.rstrip(":"), section_style))
            story.append(HRFlowable(width="100%", thickness=0.6, color="#000000", spaceBefore=4, spaceAfter=6))
            i += 1
            continue
        if line.startswith("- "):
            bullets = []
            while i < len(lines) and lines[i].startswith("- "):
                bullets.append(lines[i][2:])
                i += 1
            story.append(ListFlowable([ListItem(Paragraph(b, bullet_style)) for b in bullets], bulletType="bullet"))
            continue
        story.append(Paragraph(line, body_style))
        i += 1

    doc.build(story)
    buf.seek(0)
    return buf

@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({"message": "Invalid JSON"}), 400

    job_desc = (data or {}).get("job_desc", "").strip()
    candidate_info = (data or {}).get("candidate_info", "").strip()
    gpt_token = (data or {}).get("gpt_token", "").strip()
    file_type = (data or {}).get("file_type", "word").strip().lower()

    if not job_desc or not candidate_info or not gpt_token:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        client = OpenAI(api_key=gpt_token)
        prompt = f"""
        You are a professional resume writer. Using the Job Description and Candidate Information provided below, generate a clean, ATS-optimized resume that strictly follows the section order and formatting rules listed here:

        ⚠️ IMPORTANT: Output must contain the **resume only** — do not include explanations, disclaimers, notes, or extra text outside of the resume.

        SECTION ORDER:

        1. **PROFESSIONAL SUMMARY** – Include **6 to 8 concise bullet points** summarizing key skills, achievements, career highlights, and qualifications aligned with the job description.

        2. **SKILLS** – Based on the Job Description and Candidate Information, extract the most relevant technical and functional skills, tools, platforms, and technologies. Then organize them into **8 to 12 skill categories**, strictly selected from the list below. 
        ⚠️ You must assign each technology to the correct category only. Do not mix unrelated tools into the wrong category. Do not invent new categories. Do not include Reporting/Analytics tools under CI/CD or any unrelated grouping.

            - Programming Languages
            - Back-End Development Frameworks
            - Front-End Technologies
            - JavaScript Frameworks & Libraries
            - Mobile App Development Frameworks
            - Cross-Platform Development
            - API Development & Integration
            - Web Development
            - Game Development Tools

            - Cloud Platforms
            - Azure Services
            - AWS Services
            - Google Cloud Services
            - Hybrid & Multi-Cloud Architectures

            - CI/CD Tools
            - DevOps Tools & Practices
            - Infrastructure as Code
            - Configuration Management Tools
            - Containerization & Orchestration
            - Monitoring & Observability Tools
            - Scripting & Automation

            - Big Data Ecosystems
            - ETL & Data Integration Tools
            - Data Warehousing Solutions
            - Database Management Systems
            - Data Lake & Lakehouse Technologies
            - Data Modeling & Architecture
            - Data Governance & Lineage

            - Machine Learning Frameworks
            - Natural Language Processing
            - Computer Vision
            - Model Training & Deployment
            - AI/ML Ops Tools
            - Data Science Tools
            - Statistical Analysis & Modeling

            - Security & Compliance Tools
            - Cloud Security
            - Network Security
            - Application Security
            - Identity & Access Management
            - Security Information and Event Management
            - Penetration Testing & Ethical Hacking

            - Automated Testing Tools
            - Performance Testing Tools
            - Test Management Tools
            - API Testing Tools
            - Unit & Integration Testing Frameworks
            - QA Processes & Methodologies

            - UI/UX Design Tools
            - Wireframing & Prototyping Tools
            - Design Systems & Pattern Libraries
            - User Research & Usability Testing

            - Version Control Systems
            - Integrated Development Environments
            - Code Collaboration Tools
            - Task & Issue Tracking Tools
            - Documentation Tools

            - Operating Systems
            - Virtualization Tools
            - Desktop & Server Administration

            - Blockchain Development
            - IoT Development & Platforms
            - Edge Computing
            - Augmented Reality / Virtual Reality
            - Quantum Computing Fundamentals

        ⚠️ MANDATORY RULES:
        - Select between **8 to 12 categories** based on the job’s focus (e.g., Java Developer, React Front-End, Data Engineer, DevOps, etc.).
        - **Always show categories in a logical and relevant order** for the job role — prioritize core skills first (e.g., Programming Languages before Tools).
        - If a category is not explicitly mentioned in the JD but clearly relevant to the role, you may include it.
        - Do **not** include categories that are unrelated to the JD.
        - Each category must contain **a minimum of 6 skills** and **a maximum of 8–12 skills**, including **both primary skills and relevant sub-skills** where applicable. For example:
        Spring Framework (Spring Boot, Spring Data, Spring MVC) or
        React.js (Hooks, Context API, Redux)
        - Include closely related or equivalent technologies even if not explicitly mentioned (e.g., if JD mentions AWS, also add Azure equivalents if applicable).
        - Ensure that all technologies listed in this section are also reflected in the **Technologies Used** lines under the WORK EXPERIENCE section.


        3. **WORK EXPERIENCE** – Merge **Work History** and **Work Experience** into a unified section. For each job role:
            - Include the Job Title, Company Name (bold), Job Location, and timeline using the format:
                ```
                [Company Name] – [Job Location]  
                [Job Title] – [Start Month Year] to [End Month Year]
                ```
            - Add **10 to 15 detailed bullet points** per role describing responsibilities, accomplishments, and impact using strong, action-oriented language.
            - Ensure the **total number of bullet points across all roles is between 35 and 45**.
            - End each job section with a line:  
                **Technologies Used:** tech1, tech2, ..., tech15  
                ⚠️ Include **a minimum of 10 to 15 technologies** per role, selected from the SKILLS section.  
                When taking the union of all "Technologies Used" across all roles, the list must **comprehensively cover the entire Skills section**.

            ⚠️ IMPORTANT: Ensure the resume length is at least **two full pages**.

        4. **CERTIFICATIONS**

        5. **EDUCATION**

        FORMATTING RULES:
        - Display the candidate’s **Name** at the top.
        - Center **Email**, **Phone Number**, and **Candidate Location** on the same line directly below the name, using the format:  
        Email: | Mobile: | Location:
        - Use 0.5-inch page margins.
        - Add a tab space before each bullet point.
        - Do not use markdown or bullet characters like "-", "*", or "•".
        - The **SKILLS** section must always follow the defined categories above—never as a plain list.
        - Always ensure the final resume spans at least 2 full pages of Word or PDF output.

        JOB DESCRIPTION:
        {job_desc}

        CANDIDATE INFORMATION:
        {candidate_info}
        """



        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You write polished, ATS-friendly resumes."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        raw_resume = resp.choices[0].message.content or ""
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": f"OpenAI error: {e}"}), 500

    resume_text = clean_markdown(raw_resume).strip()
    # print("==== Resume Text ====")
    # print(resume_text)  # debug output

    # 🚨 Prevent blank Word/PDF output
    if not resume_text:
        return jsonify({"message": "Resume generation failed: Empty response from AI"}), 500

    try:
        if file_type == "word":
            buffer = BytesIO()
            doc = create_resume_word(resume_text)
            doc.save(buffer)
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name="resume.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        elif file_type == "pdf":
            buffer = create_resume_pdf(resume_text)
            return send_file(buffer, as_attachment=True, download_name="resume.pdf", mimetype="application/pdf")
        else:
            return jsonify({"message": "Invalid file_type"}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": f"File generation error: {e}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)


