from .db import db
from .models import ApplicationModel, CompanyModel, JobModel


class CareerRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def list_opportunities(self):
        jobs = (
            JobModel.query.filter_by(is_active=True)
            .order_by(JobModel.created_at.desc(), JobModel.id.desc())
            .all()
        )
        return [job.to_opportunity_dict() for job in jobs]

    def get_opportunity(self, opportunity_id):
        job = self.session.get(JobModel, opportunity_id)
        return job.to_opportunity_dict() if job else None

    def create_opportunity(self, payload):
        company = CompanyModel.query.filter_by(name=payload["company"]).first()
        if company is None:
            company = CompanyModel(
                name=payload["company"],
                description=f"{payload['company']} career opportunities.",
            )
            self.session.add(company)

        job = JobModel(
            title=payload["title"],
            description=payload["summary"],
            salary_range=payload.get("salary_range"),
            company=company,
            location=payload["location"],
            category=payload["category"],
            work_mode=payload["work_mode"],
        )
        self.session.add(job)
        self.session.commit()
        return self.get_opportunity(job.id)

    def create_application(self, payload):
        application = ApplicationModel(
            job_id=payload["opportunity_id"],
            candidate_name=payload["applicant_name"],
            email=payload["applicant_email"],
            portfolio_url=payload.get("portfolio_url"),
            resume_link=payload.get("portfolio_url"),
            motivation=payload.get("motivation"),
            status=payload.get("status", "New"),
        )
        self.session.add(application)
        self.session.commit()
        return self.get_application(application.id)

    def get_application(self, application_id):
        application = self.session.get(ApplicationModel, application_id)
        return application.to_legacy_dict() if application else None

    def list_recent_applications(self, limit=6):
        applications = (
            ApplicationModel.query.order_by(ApplicationModel.created_at.desc(), ApplicationModel.id.desc())
            .limit(limit)
            .all()
        )
        return [application.to_legacy_dict() for application in applications]

    def list_applications(self):
        applications = ApplicationModel.query.order_by(
            ApplicationModel.created_at.desc(),
            ApplicationModel.id.desc(),
        ).all()
        return [application.to_legacy_dict() for application in applications]

    def count_applications(self):
        return ApplicationModel.query.count()
