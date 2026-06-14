from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect


db = SQLAlchemy()


SEED_OPPORTUNITIES = [
    {
        "title": "QA Automation Engineer",
        "company": "BlueOrbit Labs",
        "location": "Prishtina",
        "category": "Quality Engineering",
        "work_mode": "Hybrid",
        "salary_range": "EUR 1.4k - 2.1k",
        "summary": "Design resilient test flows, improve release confidence, and keep product quality sharp.",
    },
    {
        "title": "Frontend Tester",
        "company": "Northline Studio",
        "location": "Remote",
        "category": "UI Testing",
        "work_mode": "Remote",
        "salary_range": "EUR 1.2k - 1.8k",
        "summary": "Own browser journeys, accessibility checks, and feedback loops for polished interfaces.",
    },
    {
        "title": "API Quality Analyst",
        "company": "Pulse Grid",
        "location": "Skopje",
        "category": "Backend Testing",
        "work_mode": "On-site",
        "salary_range": "EUR 1.5k - 2.4k",
        "summary": "Stress REST endpoints, validate payload accuracy, and harden error handling for core services.",
    },
]


def get_db():
    return db.session


def init_db():
    from .models import ApplicationModel, CompanyModel, JobModel, UserModel

    _ = (ApplicationModel, CompanyModel, JobModel, UserModel)
    db.drop_all()
    db.create_all()


def _seed_database():
    from .models import CompanyModel, JobModel

    if JobModel.query.count() > 0:
        return

    companies = {}
    for item in SEED_OPPORTUNITIES:
        company = companies.get(item["company"])
        if company is None:
            company = CompanyModel(
                name=item["company"],
                description=f"{item['company']} career opportunities.",
            )
            db.session.add(company)
            companies[item["company"]] = company

        db.session.add(
            JobModel(
                title=item["title"],
                description=item["summary"],
                salary_range=item["salary_range"],
                company=company,
                location=item["location"],
                category=item["category"],
                work_mode=item["work_mode"],
            )
        )

    db.session.commit()


def _schema_needs_reset():
    required_columns = {
        "users": {"id", "username", "password"},
        "companies": {"id", "name", "description"},
        "jobs": {"id", "title", "description", "salary", "company_id", "location"},
        "applications": {"id", "candidate_name", "email", "status", "job_id", "resume_link"},
    }
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name, columns in required_columns.items():
        if table_name not in existing_tables:
            return True
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        if not columns.issubset(existing_columns):
            return True

    return False


def initialize_database(seed=True):
    if _schema_needs_reset():
        init_db()
    else:
        db.create_all()

    if seed:
        _seed_database()


def init_app(app):
    db.init_app(app)
