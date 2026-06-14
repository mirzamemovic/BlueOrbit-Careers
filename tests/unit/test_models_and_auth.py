from career_portal.api import _validate_application_payload, _validate_job_payload
from career_portal.db import db
from career_portal.models import CompanyModel, JobModel, UserModel


def test_user_model_hashes_and_checks_password(app):
    with app.app_context():
        user = UserModel(username="casey")
        user.set_password("secret123")

        assert user.password != "secret123"
        assert user.check_password("secret123") is True
        assert user.check_password("wrong") is False


def test_job_model_serializes_location_extension(app):
    with app.app_context():
        company = CompanyModel(name="BlueOrbit Labs", description="Testing careers.")
        job = JobModel(
            title="QA Engineer",
            description="Create reliable test suites.",
            salary=2200,
            company=company,
            location="Remote",
        )
        db.session.add_all([company, job])
        db.session.commit()

        serialized = job.to_dict()

        assert serialized["location"] == "Remote"
        assert serialized["company"]["name"] == "BlueOrbit Labs"


def test_job_validation_rejects_missing_location_and_invalid_company(app):
    with app.app_context():
        _payload, errors = _validate_job_payload(
            {
                "title": "QA Engineer",
                "description": "Create reliable test suites.",
                "company_id": 999,
            }
        )

        assert "location" in errors
        assert errors["company_id"] == "Company not found."


def test_application_validation_rejects_bad_email_and_resume_link(app):
    payload, errors = _validate_application_payload(
        {
            "candidate_name": "Ava",
            "email": "bad-email",
            "job_id": "not-an-id",
            "resume_link": "resume.local/file.pdf",
        }
    )

    assert payload["candidate_name"] == "Ava"
    assert "email" in errors
    assert "job_id" in errors
    assert "resume_link" in errors
