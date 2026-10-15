from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.database import Base

DEFAULT_COVER_LETTER = """Dear Hiring Manager,

I am writing to apply for the Java Developer / Java Backend Developer position at your organization.

I am a Backend Software Engineer with 2+ years of experience at Rapipay Fintech Private Limited, where I have worked extensively on building and scaling fintech and lending platforms using Java, Spring Boot, Microservices, PostgreSQL, Apache Kafka, AWS SQS, Redis, Docker, and REST APIs.

In my current role, I have:
• Designed a configurable settlement posting engine that reduced partner integration TAT by 70%.
• Developed an RBI-compliant NPA classification engine processing 100K+ loan records.
• Built Kafka-based UPI/e-NACH recovery pipelines handling 30K+ daily transactions.
• Optimized PostgreSQL queries, stored procedures, execution plans, and B-tree indexes, reducing query latency by 40% on 1M+ record tables.
• Worked on event-driven architectures and Apache Fineract LMS integrations for foreclosure and loan lifecycle automation.
• Implemented rate limiting and batch processing to handle external API limitations and improve system reliability.
• Worked with multithreading, concurrency, Redis caching, AWS SQS, and distributed microservices in production environments.

I believe my combination of strong Java/Spring Boot fundamentals, microservices experience, distributed systems knowledge, database optimization, and real-world fintech domain experience makes me a strong fit for this opportunity.

I am currently serving my notice period and would be happy to discuss how my experience can contribute to your engineering team.

Please find my resume attached for your consideration. I would appreciate the opportunity to discuss the role further.

Best Regards,
Abhishek Verma
Java Backend Developer | Spring Boot | Microservices
📞 +91-6307801566
📧 abhishek.verma.6561@gmail.com
🔗 LinkedIn: linkedin.com/in/1-abhishek-verma
🔗 GitHub: github.com/Pseudo-iitian"""

class AutoApplyProfile(Base):
    __tablename__ = "auto_apply_profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), default="Abhishek Verma")
    email = Column(String(255), default="abhishek.verma.6561@gmail.com")
    phone = Column(String(100), default="+91-6307801566")
    current_company = Column(String(255), default="Rapipay Fintech Private Limited")
    current_designation = Column(String(255), default="Backend Software Engineer")
    total_experience = Column(String(100), default="2+ Years")
    current_ctc = Column(String(100), default="8.5 LPA")
    expected_ctc = Column(String(100), default="15 - 18 LPA")
    notice_period = Column(String(100), default="Serving Notice Period (30 Days)")
    available_in_30_days = Column(Boolean, default=True)
    location = Column(String(255), default="Noida / Delhi NCR / Remote (Open to Relocate)")
    linkedin_url = Column(String(500), default="https://linkedin.com/in/1-abhishek-verma")
    github_url = Column(String(500), default="https://github.com/Pseudo-iitian")
    resume_path = Column(String(1000), default="/home/abhishek_verma/Desktop/Abhishek_Verma_Resume.pdf")
    default_portal_password = Column(String(100), default="JobApp#2026@Abhi")
    cover_letter_template = Column(Text, default=DEFAULT_COVER_LETTER)
    max_exp_allowed = Column(Float, default=3.0)
    batch_size = Column(Integer, default=5)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PortalCredential(Base):
    __tablename__ = "portal_credentials"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(255), nullable=False)
    portal_domain = Column(String(500), nullable=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    job_id = Column(Integer, nullable=True)
    apply_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AutoApplyLog(Base):
    __tablename__ = "auto_apply_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=True, index=True)
    company = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    channel = Column(String(100), default="PORTAL", index=True)  # GMAIL, PORTAL, GOOGLE_FORM, LINKEDIN
    status = Column(String(100), default="APPLIED", index=True)  # APPLIED, REJECTED_EXPERIENCE, FAILED, OPENED_IN_TAB
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
