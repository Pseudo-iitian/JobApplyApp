import os
from io import BytesIO
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "tailored_resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_tailored_resume_pdf(
    candidate_name: str,
    contact_line: str,
    target_role: str,
    target_company: str,
    tailored_summary: str,
    skills: List[str],
    tailored_bullets: List[str],
    job_id: int
) -> str:
    """
    Generates a clean, modern, single-column ATS-compliant PDF resume tailored for a specific job.
    Returns the generated PDF file path.
    """
    file_name = f"Abhishek_Verma_Tailored_Resume_{job_id}_{target_company.replace(' ', '_')}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom ATS typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        alignment=1 # Center
    )
    
    contact_style = ParagraphStyle(
        'ContactInfo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#475569'),
        alignment=1 # Center
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0284C7'), # Sky Blue
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=12,
        firstLineIndent=-10,
        spaceAfter=3
    )

    story = []

    # 1. Header (Name & Contact)
    story.append(Paragraph(candidate_name, title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph(contact_line, contact_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))

    # 2. Tailored Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading))
    story.append(Paragraph(tailored_summary, body_style))
    story.append(Spacer(1, 6))

    # 3. Core Technical Skills
    story.append(Paragraph("TECHNICAL SKILLS", section_heading))
    skills_text = f"<b>Core Backend & Languages:</b> Java 8/11/17, Spring Boot, Spring MVC, Spring Security, Hibernate/JPA, RESTful Microservices<br/>"
    skills_text += f"<b>Distributed Systems & Cloud:</b> {', '.join(skills[:12])}<br/>"
    skills_text += f"<b>Databases & Messaging:</b> PostgreSQL, MySQL, Redis, Apache Kafka, RabbitMQ<br/>"
    skills_text += f"<b>Tools & DevOps:</b> Docker, Kubernetes, AWS, Git, CI/CD, Maven, JUnit, Mockito"
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 6))

    # 4. Professional Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_heading))
    
    # Current Role
    role_header = f"<b>Backend Software Engineer (Spring Boot / Java)</b> &nbsp;|&nbsp; <i>Fintech Platform Services</i>"
    date_header = "<b>2022 – Present &nbsp;|&nbsp; Noida, India</b>"
    story.append(Paragraph(f"{role_header} <font color='#64748B'>({date_header})</font>", body_style))
    
    # Tailored Bullets highlighting target company requirements
    for bullet in tailored_bullets:
        clean_b = bullet.lstrip("•- ")
        story.append(Paragraph(f"• {clean_b}", bullet_style))
        
    story.append(Paragraph("• Architected and optimized 25+ high-throughput REST APIs and transactional PostgreSQL database schemas, reducing latency by 30%.", bullet_style))
    story.append(Paragraph("• Implemented automated integration tests with JUnit and Mockito, ensuring 99.9% uptime across production microservices.", bullet_style))
    story.append(Spacer(1, 6))

    # 5. Education
    story.append(Paragraph("EDUCATION", section_heading))
    story.append(Paragraph("<b>Bachelor of Technology in Computer Science & Engineering</b> &nbsp;|&nbsp; First Class with Distinction", body_style))

    # Build PDF
    doc.build(story)
    return file_path
