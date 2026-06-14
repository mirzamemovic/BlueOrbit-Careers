from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .db import db


def utc_now():
    return datetime.now(timezone.utc)


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def to_dict(self):
        return {"id": self.id, "username": self.username}


class CompanyModel(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)

    jobs = db.relationship("JobModel", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self, include_jobs=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }
        if include_jobs:
            data["jobs"] = [job.to_dict() for job in self.jobs]
        return data


class JobModel(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.Float, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)

    # Assignment model extension: every job now has a location.
    location = db.Column(db.String(120), nullable=False)

    category = db.Column(db.String(120), nullable=True)
    work_mode = db.Column(db.String(30), nullable=True)
    salary_range = db.Column(db.String(60), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    company = db.relationship("CompanyModel", back_populates="jobs")
    applications = db.relationship(
        "ApplicationModel",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_company=True, include_applications=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "salary": self.salary,
            "company_id": self.company_id,
            "location": self.location,
            "category": self.category,
            "work_mode": self.work_mode,
            "salary_range": self.salary_range,
            "is_active": self.is_active,
            "application_count": len(self.applications),
        }
        if include_company and self.company:
            data["company"] = self.company.to_dict()
        if include_applications:
            data["applications"] = [application.to_dict(include_job=False) for application in self.applications]
        return data

    def to_opportunity_dict(self):
        company_name = self.company.name if self.company else ""
        return {
            "id": self.id,
            "title": self.title,
            "company": company_name,
            "location": self.location,
            "category": self.category or "General",
            "work_mode": self.work_mode or "Hybrid",
            "salary_range": self.salary_range or (str(self.salary) if self.salary is not None else ""),
            "summary": self.description,
            "is_active": 1 if self.is_active else 0,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "application_count": len(self.applications),
        }


class ApplicationModel(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="New")
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)

    resume_link = db.Column(db.String(500), nullable=True)
    portfolio_url = db.Column(db.String(500), nullable=True)
    motivation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    job = db.relationship("JobModel", back_populates="applications")

    def to_dict(self, include_job=True):
        data = {
            "id": self.id,
            "candidate_name": self.candidate_name,
            "email": self.email,
            "status": self.status,
            "job_id": self.job_id,
            "resume_link": self.resume_link,
        }
        if include_job and self.job:
            data["job"] = self.job.to_dict(include_company=True)
        return data

    def to_legacy_dict(self):
        job = self.job
        company = job.company if job else None
        return {
            "id": self.id,
            "opportunity_id": self.job_id,
            "applicant_name": self.candidate_name,
            "applicant_email": self.email,
            "portfolio_url": self.portfolio_url or self.resume_link or "",
            "motivation": self.motivation or "",
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "opportunity_title": job.title if job else "",
            "opportunity_company": company.name if company else "",
        }
