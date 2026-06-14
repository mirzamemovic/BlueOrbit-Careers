from career_portal.db import get_db
from career_portal.repositories import CareerRepository
from career_portal.services import create_opportunity
from career_portal.services import submit_application


def test_repository_persists_opportunity_and_application(app):
    with app.app_context():
        repo = CareerRepository(get_db())

        opportunity = create_opportunity(
            repo,
            {
                "title": "Release Tester",
                "company": "Orbit QA",
                "location": "Belgrade",
                "category": "Release Engineering",
                "work_mode": "Hybrid",
                "salary_range": "EUR 1.6k - 2.2k",
                "summary": "Coordinate release checks, smoke suites, and final sign-off confidence.",
            },
        )

        application = submit_application(
            repo,
            opportunity["id"],
            {
                "applicant_name": "Noa Finch",
                "applicant_email": "noa@example.com",
                "portfolio_url": "https://noa.dev",
                "motivation": "I build stable release pipelines and practical quality guardrails.",
            },
            lambda *_args: None,
        )

        refreshed_opportunity = repo.get_opportunity(opportunity["id"])
        recent = repo.list_recent_applications(limit=1)

        assert refreshed_opportunity["application_count"] == 1
        assert application["opportunity_title"] == "Release Tester"
        assert recent[0]["applicant_name"] == "Noa Finch"


def test_list_applications_returns_joined_opportunity_metadata(app):
    with app.app_context():
        repo = CareerRepository(get_db())
        opportunity = repo.create_opportunity(
            {
                "title": "API Reliability Analyst",
                "company": "Pulse Grid",
                "location": "Remote",
                "category": "Backend Testing",
                "work_mode": "Remote",
                "salary_range": "EUR 1.8k - 2.5k",
                "summary": "Track API reliability trends and tighten error handling across services.",
            }
        )
        repo.create_application(
            {
                "opportunity_id": opportunity["id"],
                "applicant_name": "Lena Snow",
                "applicant_email": "lena@example.com",
                "portfolio_url": "https://lena.dev",
                "motivation": "I am strong at API contract testing and defensive backend QA.",
            }
        )

        applications = repo.list_applications()

        assert applications[0]["opportunity_company"] == "Pulse Grid"
        assert applications[0]["opportunity_title"] == "API Reliability Analyst"
